package car

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"log"
	"log/slog"
	"os"
	"sort"
	"time"

	"github.com/aws/aws-sdk-go-v2/service/s3"
	blockstore "github.com/ipfs/boxo/blockstore"
	blocks "github.com/ipfs/go-block-format"
	"github.com/ipfs/go-cid"
	car "github.com/ipld/go-car"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	cbg "github.com/whyrusleeping/cbor-gen"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
)

const bigShardThreshold = 2 << 20

// Store interface for interacting with the CAR store
type Store interface {
	// TODO: not really part of general interface
	CompactUserShards(ctx context.Context, actor atp.Aid, skipBigShards bool) (*CompactionStats, error)
	// TODO: not really part of general interface
	GetCompactionTargets(ctx context.Context, shardCount int) ([]*CompactionTarget, error)
	// TODO: not really part of general interface
	PingStore(ctx context.Context) error

	GetUserRepoHead(ctx context.Context, actor atp.Aid) (cid.Cid, error)
	GetUserRepoRev(ctx context.Context, actor atp.Aid) (string, error)
	ImportSlice(ctx context.Context, aid atp.Aid, since *string, carslice []byte) (cid.Cid, *DeltaSession, error)
	NewDeltaSession(ctx context.Context, actor atp.Aid, since *string) (*DeltaSession, error)
	ReadOnlySession(actor atp.Aid) (*DeltaSession, error)
	ReadActorCar(ctx context.Context, actor atp.Aid, sinceRev string, w io.Writer) error
	Stat(ctx context.Context, actor atp.Aid) ([]UserStat, error)
	WipeUserData(ctx context.Context, actor atp.Aid) error
}

// S3CarStore contains all the dependencies for interacting with the CAR store in S3
type S3CarStore struct {
	meta           *StoreMeta
	client         *s3Client
	rootDir        string
	lastShardCache lastShardCache

	log *slog.Logger
}

// NewCarStore initializes a 'S3CarStore' struct
func NewCarStore(
	ctx context.Context,
	db *database.DB,
	client *s3.Client,
	dbSchema, env, carDir string,
	logger *slog.Logger,
) (Store, error) {
	log.Println("Setting up CAR store")

	carDb := db.WithSchema(dbSchema)

	if env == "local" {
		if _, err := client.HeadBucket(ctx, &s3.HeadBucketInput{Bucket: &carDir}); err != nil {
			log.Printf("The %s bucket does not exist, attempting to create bucket...\n", carDir)
			if _, err := client.CreateBucket(ctx, &s3.CreateBucketInput{Bucket: &carDir}); err != nil {
				return nil, err
			}
			log.Println("Successfully created bucket!")
		}
	}

	meta := &StoreMeta{carDb}
	out := &S3CarStore{
		meta:    meta,
		client:  &s3Client{client: client, bucket: carDir},
		rootDir: carDir,
		lastShardCache: lastShardCache{
			source: meta,
		},
		log: logger.With("system", "carstore"),
	}
	out.lastShardCache.init()

	log.Println("Successfully setup CAR store!")

	return out, nil
}

// func (cs *S3CarStore) checkLastShardCache(user atp.Uid) *Shard {
// 	return cs.lastShardCache.check(user)
// }

func (cs *S3CarStore) removeLastShardCache(actor atp.Aid) {
	cs.lastShardCache.remove(actor)
}

func (cs *S3CarStore) putLastShardCache(ls *Shard) {
	cs.lastShardCache.put(ls)
}

func (cs *S3CarStore) getLastShard(ctx context.Context, actor atp.Aid) (*Shard, error) {
	return cs.lastShardCache.get(ctx, actor)
}

// PingStore checks that the S3 car store bucket exists
func (cs *S3CarStore) PingStore(ctx context.Context) error {
	if err := cs.client.checkConnection(ctx); err != nil {
		return err
	}

	return nil
}

// ErrRepoBaseMismatch error returned when the root revision differs from the requested revision
var ErrRepoBaseMismatch = fmt.Errorf("attempted a delta session on top of the wrong previous head")

// NewDeltaSession initializes a 'DeltaSession' struct
func (cs *S3CarStore) NewDeltaSession(ctx context.Context, actor atp.Aid, since *string) (*DeltaSession, error) {
	ctx, span := otel.Tracer("carstore").Start(ctx, "NewSession")
	defer span.End()

	// TODO: ensure that we don't write updates on top of the wrong head
	// this needs to be a compare and swap type operation
	lastShard, err := cs.getLastShard(ctx, actor)
	if err != nil {
		return nil, err
	}

	if since != nil && *since != lastShard.Rev {
		return nil, fmt.Errorf("revision mismatch: %s != %s: %w", *since, lastShard.Rev, ErrRepoBaseMismatch)
	}

	return &DeltaSession{
		blks: make(map[cid.Cid]blocks.Block),
		base: &actorView{
			actor:    actor,
			cs:       cs.meta,
			client:   cs.client,
			prefetch: true,
			cache:    make(map[cid.Cid]blocks.Block),
		},
		actor:   actor,
		baseCid: lastShard.Root.CID,
		cs:      cs,
		seq:     lastShard.Seq + 1,
		lastRev: lastShard.Rev,
	}, nil
}

// ReadOnlySession initializes a 'DeltaSession' struct with read only capabilities
func (cs *S3CarStore) ReadOnlySession(actor atp.Aid) (*DeltaSession, error) {
	return &DeltaSession{
		base: &actorView{
			actor:    actor,
			cs:       cs.meta,
			client:   cs.client,
			prefetch: false,
			cache:    make(map[cid.Cid]blocks.Block),
		},
		readonly: true,
		actor:    actor,
		cs:       cs,
	}, nil
}

// ReadActorCar reads an entire CAR file for a specific revision into a data stream
func (cs *S3CarStore) ReadActorCar(
	ctx context.Context,
	actor atp.Aid,
	sinceRev string,
	shardOut io.Writer,
) error {
	ctx, span := otel.Tracer("carstore").Start(ctx, "ReadActorCar")
	defer span.End()

	var earlySeq int
	if sinceRev != "" {
		var err error
		earlySeq, err = cs.meta.SeqForRev(ctx, actor, sinceRev)
		if err != nil {
			return err
		}
	}

	shards, err := cs.meta.GetActorShardsDesc(ctx, actor, earlySeq)
	if err != nil {
		return err
	}

	if len(shards) == 0 {
		return fmt.Errorf("no data found for actor %d", actor)
	}

	// fast path!
	if err := car.WriteHeader(&car.CarHeader{
		Roots:   []cid.Cid{shards[0].Root.CID},
		Version: 1,
	}, shardOut); err != nil {
		return err
	}

	for _, sh := range shards {
		if err := cs.writeShardBlocks(ctx, sh, shardOut); err != nil {
			return err
		}
	}

	return nil
}

// inner loop part of ReadActorCar
// copy shard blocks from disk to Writer
func (cs *S3CarStore) writeShardBlocks(ctx context.Context, sh *Shard, shardOut io.Writer) error {
	_, span := otel.Tracer("carstore").Start(ctx, "writeShardBlocks")
	defer span.End()

	obj, err := cs.client.readFile(ctx, sh.Path, &sh.DataStart)
	if err != nil {
		return err
	}
	defer func() {
		if closeErr := obj.Body.Close(); closeErr != nil {
			cs.log.WarnContext(ctx, "Error closing S3 object body", "error", closeErr, "path", sh.Path)
		}
	}()

	_, err = io.Copy(shardOut, obj.Body)
	if err != nil {
		return err
	}

	return nil
}

// inner loop part of compactBucket
func (cs *S3CarStore) iterateShardBlocks(ctx context.Context, sh *Shard, cb func(blk blocks.Block) error) error {
	fi, err := os.Open(sh.Path)
	if err != nil {
		return err
	}
	defer func() {
		if closeErr := fi.Close(); closeErr != nil {
			cs.log.WarnContext(ctx, "Error closing file", "error", closeErr, "path", sh.Path)
		}
	}()

	rr, err := car.NewCarReader(fi)
	if err != nil {
		return fmt.Errorf("opening shard car: %w", err)
	}

	for {
		blk, err := rr.Next()
		if err != nil {
			if errors.Is(err, io.EOF) {
				return nil
			}
			return err
		}

		if err := cb(blk); err != nil {
			return err
		}
	}
}

func (cs *S3CarStore) putShard(ctx context.Context, shard *Shard, brefs []*BlockRef, nocache bool) error {
	ctx, span := otel.Tracer("carstore").Start(ctx, "putShard")
	defer span.End()

	err := cs.meta.PutShardAndRefs(ctx, shard, brefs)
	if err != nil {
		return err
	}

	if !nocache {
		cs.putLastShardCache(shard)
	}

	return nil
}

// ErrNotFound error for not finding a cid
var ErrNotFound = errors.New("cid not found")

// BlockDiff gets the diff between the old blockstore and the new one
func BlockDiff(
	ctx context.Context,
	bs blockstore.Blockstore,
	oldroot cid.Cid,
	newcids map[cid.Cid]blocks.Block,
) (map[cid.Cid]bool, error) {
	ctx, span := otel.Tracer("repo").Start(ctx, "BlockDiff")
	defer span.End()

	if !oldroot.Defined() {
		return map[cid.Cid]bool{}, nil
	}

	// walk the entire 'new' portion of the tree, marking all referenced cids as 'keep'
	keepset := make(map[cid.Cid]bool)
	for c := range newcids {
		keepset[c] = true
		oblk, err := bs.Get(ctx, c)
		if err != nil {
			return nil, fmt.Errorf("get failed in new tree: %w", err)
		}

		if err := cbg.ScanForLinks(bytes.NewReader(oblk.RawData()), func(lnk cid.Cid) {
			keepset[lnk] = true
		}); err != nil {
			return nil, err
		}
	}

	if keepset[oldroot] {
		// this should probably never happen, but is technically correct
		return nil, ErrNotFound
	}

	// next, walk the old tree from the root, recursing on cids *not* in the keepset.
	dropset := make(map[cid.Cid]bool)
	dropset[oldroot] = true
	queue := []cid.Cid{oldroot}

	for len(queue) > 0 {
		c := queue[0]
		queue = queue[1:]

		oblk, err := bs.Get(ctx, c)
		if err != nil {
			return nil, fmt.Errorf("get failed in old tree: %w", err)
		}

		if err := cbg.ScanForLinks(bytes.NewReader(oblk.RawData()), func(lnk cid.Cid) {
			if lnk.Prefix().Codec != cid.DagCBOR {
				return
			}

			if !keepset[lnk] {
				dropset[lnk] = true
				queue = append(queue, lnk)
			}
		}); err != nil {
			return nil, err
		}
	}

	return dropset, nil
}

// CalcDiff wrapper around 'BlockDiff' and writes the diff to the 'DeltaSession' instance
func (ds *DeltaSession) CalcDiff(ctx context.Context) error {
	rmcids, err := BlockDiff(ctx, ds, ds.baseCid, ds.blks)
	if err != nil {
		return fmt.Errorf("block diff failed (base=%s,rev=%s): %w", ds.baseCid, ds.lastRev, err)
	}

	ds.rmcids = rmcids
	return nil
}

// ImportSlice reads a slice of bytes and writes it as a CAR file
func (cs *S3CarStore) ImportSlice(
	ctx context.Context,
	uid atp.Aid,
	since *string,
	carslice []byte,
) (cid.Cid, *DeltaSession, error) {
	ctx, span := otel.Tracer("carstore").Start(ctx, "ImportSlice")
	defer span.End()

	carr, err := car.NewCarReader(bytes.NewReader(carslice))
	if err != nil {
		return cid.Undef, nil, err
	}

	if len(carr.Header.Roots) != 1 {
		return cid.Undef, nil, fmt.Errorf(
			"invalid car file, header must have a single root (has %d)",
			len(carr.Header.Roots),
		)
	}

	ds, err := cs.NewDeltaSession(ctx, uid, since)
	if err != nil {
		return cid.Undef, nil, fmt.Errorf("new delta session failed: %w", err)
	}

	for {
		blk, err := carr.Next()
		if err != nil {
			if errors.Is(err, io.EOF) {
				break
			}
			return cid.Undef, nil, err
		}

		if err := ds.Put(ctx, blk); err != nil {
			return cid.Undef, nil, err
		}
	}

	return carr.Header.Roots[0], ds, nil
}

// GetUserRepoHead get the head CID for a user
func (cs *S3CarStore) GetUserRepoHead(ctx context.Context, user atp.Aid) (cid.Cid, error) {
	lastShard, err := cs.getLastShard(ctx, user)
	if err != nil {
		return cid.Undef, err
	}
	if lastShard.ID == 0 {
		return cid.Undef, nil
	}

	return lastShard.Root.CID, nil
}

// GetUserRepoRev get the head revision for a user
func (cs *S3CarStore) GetUserRepoRev(ctx context.Context, user atp.Aid) (string, error) {
	lastShard, err := cs.getLastShard(ctx, user)
	if err != nil {
		return "", err
	}

	if lastShard.ID == 0 {
		return "", nil
	}

	return lastShard.Rev, nil
}

// WipeUserData deletes an actor's CAR files and DB metadata
func (cs *S3CarStore) WipeUserData(ctx context.Context, actor atp.Aid) error {
	shards, err := cs.meta.GetActorShards(ctx, actor)
	if err != nil {
		return err
	}

	if err := cs.deleteShards(ctx, actor, shards); err != nil {
		return err
	}

	cs.removeLastShardCache(actor)

	return nil
}

func (cs *S3CarStore) deleteShards(ctx context.Context, user atp.Aid, shs []*Shard) error {
	ctx, span := otel.Tracer("carstore").Start(ctx, "deleteShards")
	defer span.End()

	deleteSlice := func(ctx context.Context, subs []*Shard) error {
		ids := make([]uint, len(subs))
		seqs := make([]int, len(subs))
		for i, sh := range subs {
			ids[i] = sh.ID
			seqs[i] = sh.Seq
		}

		err := cs.meta.DeleteShardsAndRefs(ctx, ids)
		if err != nil {
			return err
		}

		if err := cs.client.deleteShardFiles(ctx, user, seqs); err != nil {
			cs.log.ErrorContext(ctx, "Error deleting CAR files from store", "error", err)
			return err
		}

		return nil
	}

	chunkSize := 2000
	for i := 0; i < len(shs); i += chunkSize {
		sl := shs[i:]
		if len(sl) > chunkSize {
			sl = sl[:chunkSize]
		}

		if err := deleteSlice(ctx, sl); err != nil {
			return err
		}
	}

	return nil
}

// UserStat struct contains all the root CID for a CAR file
type UserStat struct {
	Seq     int
	Root    string
	Created time.Time
}

// Stat returns a slice of root CIDs
func (cs *S3CarStore) Stat(ctx context.Context, aid atp.Aid) ([]UserStat, error) {
	shards, err := cs.meta.GetActorShards(ctx, aid)
	if err != nil {
		return nil, err
	}

	var out []UserStat
	for _, s := range shards {
		out = append(out, UserStat{
			Seq:     s.Seq,
			Root:    s.Root.CID.String(),
			Created: s.CreatedAt,
		})
	}

	return out, nil
}

type shardStat struct {
	ID    uint
	Dirty int
	Seq   int
	Total int

	refs []*BlockRef
}

func (s shardStat) dirtyFrac() float64 {
	return float64(s.Dirty) / float64(s.Total)
}

func aggrRefs(brefs []*BlockRef, shards map[uint]*Shard) []shardStat {
	byId := make(map[uint]*shardStat)

	for _, br := range brefs {
		s, ok := byId[br.Shard]
		if !ok {
			s = &shardStat{
				ID:  br.Shard,
				Seq: shards[br.Shard].Seq,
			}
			byId[br.Shard] = s
		}

		s.Total++

		s.refs = append(s.refs, br)
	}

	var out []shardStat
	for _, s := range byId {
		out = append(out, *s)
	}

	sort.Slice(out, func(i, j int) bool {
		return out[i].Seq < out[j].Seq
	})

	return out
}

type compBucket struct {
	shards []shardStat

	cleanBlocks int
	expSize     int
}

func (cb *compBucket) shouldCompact() bool {
	if len(cb.shards) == 0 {
		return false
	}

	if len(cb.shards) > 5 {
		return true
	}

	var frac float64
	for _, s := range cb.shards {
		frac += s.dirtyFrac()
	}
	frac /= float64(len(cb.shards))

	if len(cb.shards) > 3 && frac > 0.2 {
		return true
	}

	return frac > 0.4
}

func (cb *compBucket) addShardStat(ss shardStat) {
	cb.cleanBlocks += (ss.Total - ss.Dirty)
	cb.shards = append(cb.shards, ss)
}

func (cb *compBucket) isEmpty() bool {
	return len(cb.shards) == 0
}

func (cs *S3CarStore) openNewCompactedShardFile(user atp.Aid, seq int) (*os.File, string, error) {
	// TODO: some overwrite protections
	// NOTE CreateTemp is used for creating a non-colliding file, but we keep it and don't delete it so don't think of it as "temporary".
	// This creates "sh-%d-%d%s" with some random stuff in the last position
	fi, err := os.CreateTemp(cs.rootDir, fnameForShard(user, seq))
	if err != nil {
		return nil, "", err
	}

	return fi, fi.Name(), nil
}

// getBlockRefsForShards is a prep function for CompactUserShards
func (cs *S3CarStore) getBlockRefsForShards(ctx context.Context, shardIds []uint) ([]*BlockRef, error) {
	ctx, span := otel.Tracer("carstore").Start(ctx, "getBlockRefsForShards")
	defer span.End()

	span.SetAttributes(attribute.Int("shards", len(shardIds)))

	out, err := cs.meta.GetBlockRefsForShards(ctx, shardIds)
	if err != nil {
		return nil, err
	}

	span.SetAttributes(attribute.Int("refs", len(out)))

	return out, nil
}

func (cs *S3CarStore) shardSize(ctx context.Context, sh *Shard) (int64, error) {
	st, err := os.Stat(sh.Path)
	if err != nil {
		if os.IsNotExist(err) {
			cs.log.WarnContext(
				ctx,
				"missing shard, return size of zero",
				"path",
				sh.Path,
				"shard",
				sh.ID,
				"system",
				"carstore",
			)
			return 0, nil
		}
		return 0, fmt.Errorf("stat %q: %w", sh.Path, err)
	}

	return st.Size(), nil
}

// CompactionStats contains all the CAR metadata for a user to compact shards
// TODO: This may be deprecated?
type CompactionStats struct {
	TotalRefs     int `json:"totalRefs"`
	StartShards   int `json:"startShards"`
	NewShards     int `json:"newShards"`
	SkippedShards int `json:"skippedShards"`
	ShardsDeleted int `json:"shardsDeleted"`
	DupeCount     int `json:"dupeCount"`
}

// CompactUserShards compacts user CAR shards
func (cs *S3CarStore) CompactUserShards(
	ctx context.Context,
	actor atp.Aid,
	skipBigShards bool,
) (*CompactionStats, error) {
	ctx, span := otel.Tracer("carstore").Start(ctx, "CompactUserShards")
	defer span.End()

	span.SetAttributes(attribute.Int64("actor", int64(uint64(actor)))) //nolint:gosec

	shards, err := cs.meta.GetActorShards(ctx, actor)
	if err != nil {
		return nil, err
	}

	if skipBigShards {
		// Since we generally expect shards to start bigger and get smaller,
		// and because we want to avoid compacting non-adjacent shards
		// together, and because we want to avoid running a stat on every
		// single shard (can be expensive for repos that haven't been compacted
		// in a while) we only skip a prefix of shard files that are over the
		// threshold. this may end up not skipping some shards that are over
		// the threshold if a below-threshold shard occurs before them, but
		// since this is a heuristic and imperfect optimization, that is
		// acceptable.
		var skip int
		for i, sh := range shards {
			size, serr := cs.shardSize(ctx, sh)
			if serr != nil {
				return nil, fmt.Errorf("could not check size of shard file: %w", serr)
			}

			if size > bigShardThreshold {
				skip = i + 1
			} else {
				break
			}
		}
		shards = shards[skip:]
	}

	span.SetAttributes(attribute.Int("shards", len(shards)))

	var shardIds []uint
	for _, s := range shards {
		shardIds = append(shardIds, s.ID)
	}

	shardsById := make(map[uint]*Shard)
	for _, s := range shards {
		shardsById[s.ID] = s
	}

	brefs, err := cs.getBlockRefsForShards(ctx, shardIds)
	if err != nil {
		return nil, fmt.Errorf("getting block refs failed: %w", err)
	}

	span.SetAttributes(attribute.Int("blockRefs", len(brefs)))

	results := aggrRefs(brefs, shardsById)
	var sum int
	for _, r := range results {
		sum += r.Total
	}

	lowBound := 20
	n := 10
	// we want to *aim* for N shards per user
	// the last several should be left small to allow easy loading from disk
	// for updates (since recent blocks are most likely needed for edits)
	// the beginning of the list should be some sort of exponential fall-off
	// with the area under the curve targeted by the total number of blocks we
	// have
	var threshs []int
	tot := len(brefs)
	for range make([]struct{}, n) {
		v := max(tot/2, lowBound)
		tot /= 2
		threshs = append(threshs, v)
	}

	thresholdForPosition := func(i int) int {
		if i >= len(threshs) {
			return lowBound
		}
		return threshs[i]
	}

	cur := new(compBucket)
	cur.expSize = thresholdForPosition(0)
	var compactionQueue []*compBucket
	for i, r := range results {
		cur.addShardStat(r)

		if cur.cleanBlocks > cur.expSize || i > len(results)-3 {
			compactionQueue = append(compactionQueue, cur)
			cur = &compBucket{
				expSize: thresholdForPosition(len(compactionQueue)),
			}
		}
	}
	if !cur.isEmpty() {
		compactionQueue = append(compactionQueue, cur)
	}

	stats := &CompactionStats{
		StartShards: len(shards),
		TotalRefs:   len(brefs),
	}

	removedShards := make(map[uint]bool)
	for _, b := range compactionQueue {
		if !b.shouldCompact() {
			stats.SkippedShards += len(b.shards)
			continue
		}

		if err := cs.compactBucket(ctx, actor, b, shardsById); err != nil {
			return nil, fmt.Errorf("compact bucket: %w", err)
		}

		stats.NewShards++

		todelete := make([]*Shard, 0, len(b.shards))
		for _, s := range b.shards {
			removedShards[s.ID] = true
			sh, ok := shardsById[s.ID]
			if !ok {
				return nil, fmt.Errorf("missing shard to delete")
			}

			todelete = append(todelete, sh)
		}

		stats.ShardsDeleted += len(todelete)
		if err := cs.deleteShards(ctx, actor, todelete); err != nil {
			return nil, fmt.Errorf("deleting shards: %w", err)
		}
	}

	return stats, nil
}

// GetCompactionTargets queries DB for the count of CAR shards for each user
func (cs *S3CarStore) GetCompactionTargets(ctx context.Context, shardCount int) ([]*CompactionTarget, error) {
	ctx, span := otel.Tracer("carstore").Start(ctx, "GetCompactionTargets")
	defer span.End()

	return cs.meta.GetCompactionTargets(ctx, shardCount)
}

func (cs *S3CarStore) compactBucket(
	ctx context.Context,
	user atp.Aid,
	b *compBucket,
	shardsById map[uint]*Shard,
) error {
	ctx, span := otel.Tracer("carstore").Start(ctx, "compactBucket")
	defer span.End()

	span.SetAttributes(attribute.Int("shards", len(b.shards)))

	last := b.shards[len(b.shards)-1]
	lastsh := shardsById[last.ID]
	fi, path, err := cs.openNewCompactedShardFile(user, last.Seq)
	if err != nil {
		return fmt.Errorf("opening new file: %w", err)
	}
	defer func() {
		if closeErr := fi.Close(); closeErr != nil {
			cs.log.WarnContext(ctx, "Error closing file", "error", closeErr, "seq", last.Seq)
		}
	}()

	root := lastsh.Root.CID

	hnw, err := writeCarHeader(fi, root)
	if err != nil {
		return err
	}

	offset := hnw
	var nbrefs []*BlockRef
	written := make(map[cid.Cid]bool)
	for _, s := range b.shards {
		sh := shardsById[s.ID]
		if err := cs.iterateShardBlocks(ctx, sh, func(blk blocks.Block) error {
			if written[blk.Cid()] {
				return nil
			}

			nw, err := LdWrite(fi, blk.Cid().Bytes(), blk.RawData())
			if err != nil {
				return fmt.Errorf("failed to write block: %w", err)
			}

			nbrefs = append(nbrefs, &BlockRef{
				Cid:        atp.DbCID{CID: blk.Cid()},
				ByteOffset: offset,
				Uid:        user,
			})

			offset += nw
			written[blk.Cid()] = true
			return nil
		}); err != nil {
			// If we ever fail to iterate a shard file because its
			// corrupted, just log an error and skip the shard
			cs.log.ErrorContext(ctx, "iterating blocks in shard", "shard", s.ID, "err", err, "uid", user)
		}
	}

	shard := Shard{
		Root:      atp.DbCID{CID: root},
		DataStart: hnw,
		Seq:       lastsh.Seq,
		Path:      path,
		Uid:       user,
		Rev:       lastsh.Rev,
	}

	if err := cs.putShard(ctx, &shard, nbrefs, true); err != nil {
		// if writing the shard fails, we should also delete the file
		_ = fi.Close()

		if err2 := os.Remove(fi.Name()); err2 != nil {
			cs.log.ErrorContext(
				ctx,
				"failed to remove shard file after failed db transaction",
				"path",
				fi.Name(),
				"err",
				err2,
			)
		}

		return err
	}
	return nil
}

// shardWriter.writeNewShard called from inside DeltaSession.CloseWithRoot
type shardWriter interface {
	// writeNewShard stores blocks in `blks` arg and creates a new shard to propagate out to our firehose
	writeNewShard(
		ctx context.Context,
		root cid.Cid,
		rev string,
		user atp.Aid,
		seq int,
		blks map[cid.Cid]blocks.Block,
		rmcids map[cid.Cid]bool,
	) ([]byte, error)
}

func (cs *S3CarStore) writeNewShard(
	ctx context.Context,
	root cid.Cid,
	rev string,
	user atp.Aid,
	seq int,
	blks map[cid.Cid]blocks.Block,
	rmcids map[cid.Cid]bool,
) ([]byte, error) {
	buf := new(bytes.Buffer)
	hnw, err := writeCarHeader(buf, root)
	if err != nil {
		return nil, fmt.Errorf("failed to write car header: %w", err)
	}

	// TODO: writing these blocks in map traversal order is bad, I believe the
	// optimal ordering will be something like reverse-write-order, but random
	// is definitely not it

	offset := hnw
	var brefs []*BlockRef
	for k, blk := range blks {
		nw, nerr := LdWrite(buf, k.Bytes(), blk.RawData())
		if nerr != nil {
			return nil, fmt.Errorf("failed to write block: %w", nerr)
		}

		brefs = append(brefs, &BlockRef{
			Cid:        atp.DbCID{CID: k},
			ByteOffset: offset,
			Uid:        user,
		})

		offset += nw
	}

	start := time.Now()
	path, err := cs.client.writeNewShardFile(ctx, user, seq, buf.Bytes())
	if err != nil {
		return nil, fmt.Errorf("failed to write shard file: %w", err)
	}
	writeShardFileDuration.Observe(time.Since(start).Seconds())

	shard := Shard{
		Root:      atp.DbCID{CID: root},
		DataStart: hnw,
		Seq:       seq,
		Path:      path,
		Uid:       user,
		Rev:       rev,
	}

	start = time.Now()
	if err := cs.putShard(ctx, &shard, brefs, false); err != nil {
		return nil, err
	}
	writeShardMetadataDuration.Observe(time.Since(start).Seconds())

	return buf.Bytes(), nil
}
