package car

import (
	"bufio"
	"bytes"
	"context"
	"fmt"
	"io"
	"log/slog"
	"os"
	"path/filepath"
	"sort"
	"sync/atomic"
	"time"

	blockstore "github.com/ipfs/boxo/blockstore"
	blocks "github.com/ipfs/go-block-format"
	"github.com/ipfs/go-cid"
	cbor "github.com/ipfs/go-ipld-cbor"
	ipld "github.com/ipfs/go-ipld-format"
	car "github.com/ipld/go-car"
	carutil "github.com/ipld/go-car/util"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	cbg "github.com/whyrusleeping/cbor-gen"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"

	"github.com/referendumApp/referendumServices/internal/config"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
)

var blockGetTotalCounter = promauto.NewCounterVec(prometheus.CounterOpts{
	Name: "carstore_block_get_total",
	Help: "carstore get queries",
}, []string{"usrskip", "cache"})

var blockGetTotalCounterUsrskip = blockGetTotalCounter.WithLabelValues("true", "miss")
var blockGetTotalCounterCached = blockGetTotalCounter.WithLabelValues("false", "hit")
var blockGetTotalCounterNormal = blockGetTotalCounter.WithLabelValues("false", "miss")

const MaxSliceLength = 2 << 20

const BigShardThreshold = 2 << 20

func Initialize(cfg config.Config, db *database.DB) (Store, error) {
	slog.Info("Setting up CAR store")

	carDb := db.WithSchema(cfg.CarDBSchema)

	if err := os.MkdirAll(cfg.CarDir, os.ModePerm); err != nil {
		slog.Error("Error creating CAR store directory", "dir", cfg.CarDir)
		return nil, err
	}

	slog.Info("Successfully setup CAR store!")

	return NewCarStore(carDb, []string{cfg.CarDir})
}

type Store interface {
	// TODO: not really part of general interface
	CompactUserShards(ctx context.Context, user atp.Uid, skipBigShards bool) (*CompactionStats, error)
	// TODO: not really part of general interface
	GetCompactionTargets(ctx context.Context, shardCount int) ([]*CompactionTarget, error)

	GetUserRepoHead(ctx context.Context, user atp.Uid) (cid.Cid, error)
	GetUserRepoRev(ctx context.Context, user atp.Uid) (string, error)
	ImportSlice(ctx context.Context, uid atp.Uid, since *string, carslice []byte) (cid.Cid, *DeltaSession, error)
	NewDeltaSession(ctx context.Context, user atp.Uid, since *string) (*DeltaSession, error)
	ReadOnlySession(user atp.Uid) (*DeltaSession, error)
	ReadUserCar(ctx context.Context, user atp.Uid, sinceRev string, incremental bool, w io.Writer) error
	Stat(ctx context.Context, usr atp.Uid) ([]UserStat, error)
	WipeUserData(ctx context.Context, user atp.Uid) error
}

type FileCarStore struct {
	meta     *StoreMeta
	rootDirs []string

	lastShardCache lastShardCache

	log *slog.Logger
}

func NewCarStore(db *database.DB, roots []string) (Store, error) {
	for _, root := range roots {
		if _, err := os.Stat(root); err != nil {
			if !os.IsNotExist(err) {
				return nil, err
			}

			if err := os.Mkdir(root, 0775); err != nil {
				return nil, err
			}
		}
	}

	meta := &StoreMeta{db: db}
	out := &FileCarStore{
		meta:     meta,
		rootDirs: roots,
		lastShardCache: lastShardCache{
			source: meta,
		},
		log: slog.Default().With("system", "carstore"),
	}
	out.lastShardCache.Init()
	return out, nil
}

// userView needs these things to get into the underlying block store
// implemented by StoreMeta
type userViewSource interface {
	HasUidCid(ctx context.Context, user atp.Uid, k cid.Cid) (bool, error)
	LookupBlockRef(ctx context.Context, k cid.Cid) (path string, offset int64, user atp.Uid, err error)
}

// wrapper into a block store that keeps track of which user we are working on behalf of
type userView struct {
	cs   userViewSource
	user atp.Uid

	cache    map[cid.Cid]blocks.Block
	prefetch bool
}

var _ blockstore.Blockstore = (*userView)(nil)

func (uv *userView) HashOnRead(hor bool) {
	//noop
}

func (uv *userView) Has(ctx context.Context, k cid.Cid) (bool, error) {
	_, have := uv.cache[k]
	if have {
		return have, nil
	}
	return uv.cs.HasUidCid(ctx, uv.user, k)
}

var CacheHits int64
var CacheMiss int64

func (uv *userView) Get(ctx context.Context, k cid.Cid) (blocks.Block, error) {
	if !k.Defined() {
		return nil, fmt.Errorf("attempted to 'get' undefined cid")
	}
	if uv.cache != nil {
		blk, ok := uv.cache[k]
		if ok {
			blockGetTotalCounterCached.Add(1)
			atomic.AddInt64(&CacheHits, 1)

			return blk, nil
		}
	}
	atomic.AddInt64(&CacheMiss, 1)

	path, offset, user, err := uv.cs.LookupBlockRef(ctx, k)
	if err != nil {
		return nil, err
	}
	if path == "" {
		return nil, ipld.ErrNotFound{Cid: k}
	}

	prefetch := uv.prefetch
	if user != uv.user {
		blockGetTotalCounterUsrskip.Add(1)
		prefetch = false
	} else {
		blockGetTotalCounterNormal.Add(1)
	}

	if prefetch {
		return uv.prefetchRead(ctx, k, path, offset)
	} else {
		return uv.singleRead(k, path, offset)
	}
}

const prefetchThreshold = 512 << 10

func (uv *userView) prefetchRead(ctx context.Context, k cid.Cid, path string, offset int64) (blocks.Block, error) {
	_, span := otel.Tracer("carstore").Start(ctx, "getLastShard")
	defer span.End()

	fi, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer fi.Close()

	st, err := fi.Stat()
	if err != nil {
		return nil, fmt.Errorf("stat file for prefetch: %w", err)
	}

	span.SetAttributes(attribute.Int64("shard_size", st.Size()))

	if st.Size() > prefetchThreshold {
		span.SetAttributes(attribute.Bool("no_prefetch", true))
		return doBlockRead(fi, k, offset)
	}

	cr, err := car.NewCarReader(fi)
	if err != nil {
		return nil, err
	}

	for {
		blk, err := cr.Next()
		if err != nil {
			if err == io.EOF {
				break
			}
			return nil, err
		}

		uv.cache[blk.Cid()] = blk
	}

	outblk, ok := uv.cache[k]
	if !ok {
		return nil, fmt.Errorf("requested block was not found in car slice")
	}

	return outblk, nil
}

func (uv *userView) singleRead(k cid.Cid, path string, offset int64) (blocks.Block, error) {
	fi, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer fi.Close()

	return doBlockRead(fi, k, offset)
}

func doBlockRead(fi *os.File, k cid.Cid, offset int64) (blocks.Block, error) {
	seeked, err := fi.Seek(offset, io.SeekStart)
	if err != nil {
		return nil, err
	}

	if seeked != offset {
		return nil, fmt.Errorf("failed to seek to offset (%d != %d)", seeked, offset)
	}

	bufr := bufio.NewReader(fi)
	rcid, data, err := carutil.ReadNode(bufr)
	if err != nil {
		return nil, err
	}

	if rcid != k {
		return nil, fmt.Errorf("mismatch in cid on disk: %s != %s", rcid, k)
	}

	return blocks.NewBlockWithCid(data, rcid)
}

func (uv *userView) AllKeysChan(ctx context.Context) (<-chan cid.Cid, error) {
	return nil, fmt.Errorf("not implemented")
}

func (uv *userView) Put(ctx context.Context, blk blocks.Block) error {
	return fmt.Errorf("puts not supported to car view blockstores")
}

func (uv *userView) PutMany(ctx context.Context, blks []blocks.Block) error {
	return fmt.Errorf("puts not supported to car view blockstores")
}

func (uv *userView) DeleteBlock(ctx context.Context, k cid.Cid) error {
	return fmt.Errorf("deletes not supported to car view blockstore")
}

func (uv *userView) GetSize(ctx context.Context, k cid.Cid) (int, error) {
	// TODO: maybe block size should be in the database record...
	blk, err := uv.Get(ctx, k)
	if err != nil {
		return 0, err
	}

	return len(blk.RawData()), nil
}

// subset of blockstore.Blockstore that we actually use here
type minBlockstore interface {
	Get(ctx context.Context, bcid cid.Cid) (blocks.Block, error)
	Has(ctx context.Context, bcid cid.Cid) (bool, error)
	GetSize(ctx context.Context, bcid cid.Cid) (int, error)
}

type DeltaSession struct {
	blks     map[cid.Cid]blocks.Block
	rmcids   map[cid.Cid]bool
	base     minBlockstore
	user     atp.Uid
	baseCid  cid.Cid
	seq      int
	readonly bool
	cs       shardWriter
	lastRev  string
}

// func (cs *FileCarStore) checkLastShardCache(user atp.Uid) *Shard {
// 	return cs.lastShardCache.check(user)
// }

func (cs *FileCarStore) removeLastShardCache(user atp.Uid) {
	cs.lastShardCache.remove(user)
}

func (cs *FileCarStore) putLastShardCache(ls *Shard) {
	cs.lastShardCache.put(ls)
}

func (cs *FileCarStore) getLastShard(ctx context.Context, user atp.Uid) (*Shard, error) {
	return cs.lastShardCache.get(ctx, user)
}

var ErrRepoBaseMismatch = fmt.Errorf("attempted a delta session on top of the wrong previous head")

func (cs *FileCarStore) NewDeltaSession(ctx context.Context, user atp.Uid, since *string) (*DeltaSession, error) {
	ctx, span := otel.Tracer("carstore").Start(ctx, "NewSession")
	defer span.End()

	// TODO: ensure that we don't write updates on top of the wrong head
	// this needs to be a compare and swap type operation
	lastShard, err := cs.getLastShard(ctx, user)
	if err != nil {
		return nil, err
	}

	if since != nil && *since != lastShard.Rev {
		return nil, fmt.Errorf("revision mismatch: %s != %s: %w", *since, lastShard.Rev, ErrRepoBaseMismatch)
	}

	return &DeltaSession{
		blks: make(map[cid.Cid]blocks.Block),
		base: &userView{
			user:     user,
			cs:       cs.meta,
			prefetch: true,
			cache:    make(map[cid.Cid]blocks.Block),
		},
		user:    user,
		baseCid: lastShard.Root.CID,
		cs:      cs,
		seq:     lastShard.Seq + 1,
		lastRev: lastShard.Rev,
	}, nil
}

func (cs *FileCarStore) ReadOnlySession(user atp.Uid) (*DeltaSession, error) {
	return &DeltaSession{
		base: &userView{
			user:     user,
			cs:       cs.meta,
			prefetch: false,
			cache:    make(map[cid.Cid]blocks.Block),
		},
		readonly: true,
		user:     user,
		cs:       cs,
	}, nil
}

// TODO: incremental is only ever called true, remove the param
func (cs *FileCarStore) ReadUserCar(ctx context.Context, user atp.Uid, sinceRev string, incremental bool, shardOut io.Writer) error {
	ctx, span := otel.Tracer("carstore").Start(ctx, "ReadUserCar")
	defer span.End()

	var earlySeq int
	if sinceRev != "" {
		var err error
		earlySeq, err = cs.meta.SeqForRev(ctx, user, sinceRev)
		if err != nil {
			return err
		}
	}

	shards, err := cs.meta.GetUserShardsDesc(ctx, user, earlySeq)
	if err != nil {
		return err
	}

	// TODO: incremental is only ever called true, so this is fine and we can remove the error check
	if !incremental && earlySeq > 0 {
		// have to do it the ugly way
		return fmt.Errorf("nyi")
	}

	if len(shards) == 0 {
		return fmt.Errorf("no data found for user %d", user)
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

// inner loop part of ReadUserCar
// copy shard blocks from disk to Writer
func (cs *FileCarStore) writeShardBlocks(ctx context.Context, sh *Shard, shardOut io.Writer) error {
	_, span := otel.Tracer("carstore").Start(ctx, "writeShardBlocks")
	defer span.End()

	fi, err := os.Open(sh.Path)
	if err != nil {
		return err
	}
	defer fi.Close()

	_, err = fi.Seek(sh.DataStart, io.SeekStart)
	if err != nil {
		return err
	}

	_, err = io.Copy(shardOut, fi)
	if err != nil {
		return err
	}

	return nil
}

// inner loop part of compactBucket
func (cs *FileCarStore) iterateShardBlocks(sh *Shard, cb func(blk blocks.Block) error) error {
	fi, err := os.Open(sh.Path)
	if err != nil {
		return err
	}
	defer fi.Close()

	rr, err := car.NewCarReader(fi)
	if err != nil {
		return fmt.Errorf("opening shard car: %w", err)
	}

	for {
		blk, err := rr.Next()
		if err != nil {
			if err == io.EOF {
				return nil
			}
			return err
		}

		if err := cb(blk); err != nil {
			return err
		}
	}
}

var _ blockstore.Blockstore = (*DeltaSession)(nil)

func (ds *DeltaSession) BaseCid() cid.Cid {
	return ds.baseCid
}

func (ds *DeltaSession) Put(ctx context.Context, b blocks.Block) error {
	if ds.readonly {
		return fmt.Errorf("cannot write to readonly deltaSession")
	}
	ds.blks[b.Cid()] = b
	return nil
}

func (ds *DeltaSession) PutMany(ctx context.Context, bs []blocks.Block) error {
	if ds.readonly {
		return fmt.Errorf("cannot write to readonly deltaSession")
	}

	for _, b := range bs {
		ds.blks[b.Cid()] = b
	}
	return nil
}

func (ds *DeltaSession) AllKeysChan(ctx context.Context) (<-chan cid.Cid, error) {
	return nil, fmt.Errorf("AllKeysChan not implemented")
}

func (ds *DeltaSession) DeleteBlock(ctx context.Context, c cid.Cid) error {
	if ds.readonly {
		return fmt.Errorf("cannot write to readonly deltaSession")
	}

	if _, ok := ds.blks[c]; !ok {
		return ipld.ErrNotFound{Cid: c}
	}

	delete(ds.blks, c)
	return nil
}

func (ds *DeltaSession) Get(ctx context.Context, c cid.Cid) (blocks.Block, error) {
	b, ok := ds.blks[c]
	if ok {
		return b, nil
	}

	return ds.base.Get(ctx, c)
}

func (ds *DeltaSession) Has(ctx context.Context, c cid.Cid) (bool, error) {
	_, ok := ds.blks[c]
	if ok {
		return true, nil
	}

	return ds.base.Has(ctx, c)
}

func (ds *DeltaSession) HashOnRead(hor bool) {
	// noop?
}

func (ds *DeltaSession) GetSize(ctx context.Context, c cid.Cid) (int, error) {
	b, ok := ds.blks[c]
	if ok {
		return len(b.RawData()), nil
	}

	return ds.base.GetSize(ctx, c)
}

func fnameForShard(user atp.Uid, seq int) string {
	return fmt.Sprintf("sh-%d-%d", user, seq)
}

func (cs *FileCarStore) dirForUser(user atp.Uid) string {
	return cs.rootDirs[int(uint(user)%uint(len(cs.rootDirs)))] // nolint:gosec
}

// func (cs *FileCarStore) openNewShardFile(ctx context.Context, user atp.Uid, seq int) (*os.File, string, error) {
// 	// TODO: some overwrite protections
// 	fname := filepath.Join(cs.dirForUser(user), fnameForShard(user, seq))
// 	fi, err := os.Create(fname)
// 	if err != nil {
// 		return nil, "", err
// 	}
//
// 	return fi, fname, nil
// }

func (cs *FileCarStore) writeNewShardFile(ctx context.Context, user atp.Uid, seq int, data []byte) (string, error) {
	_, span := otel.Tracer("carstore").Start(ctx, "writeNewShardFile")
	defer span.End()

	// TODO: some overwrite protections
	fname := filepath.Join(cs.dirForUser(user), fnameForShard(user, seq))
	if err := os.WriteFile(fname, data, 0600); err != nil {
		return "", err
	}

	return fname, nil
}

func (cs *FileCarStore) deleteShardFile(sh *Shard) error {
	return os.Remove(sh.Path)
}

// CloseWithRoot writes all new blocks in a car file to the writer with the
// given cid as the 'root'
func (ds *DeltaSession) CloseWithRoot(ctx context.Context, root cid.Cid, rev string) ([]byte, error) {
	ctx, span := otel.Tracer("carstore").Start(ctx, "CloseWithRoot")
	defer span.End()

	if ds.readonly {
		return nil, fmt.Errorf("cannot write to readonly deltaSession")
	}

	return ds.cs.writeNewShard(ctx, root, rev, ds.user, ds.seq, ds.blks, ds.rmcids)
}

func WriteCarHeader(w io.Writer, root cid.Cid) (int64, error) {
	h := &car.CarHeader{
		Roots:   []cid.Cid{root},
		Version: 1,
	}
	hb, err := cbor.DumpObject(h)
	if err != nil {
		return 0, err
	}

	hnw, err := LdWrite(w, hb)
	if err != nil {
		return 0, err
	}

	return hnw, nil
}

// shardWriter.writeNewShard called from inside DeltaSession.CloseWithRoot
type shardWriter interface {
	// writeNewShard stores blocks in `blks` arg and creates a new shard to propagate out to our firehose
	writeNewShard(ctx context.Context, root cid.Cid, rev string, user atp.Uid, seq int, blks map[cid.Cid]blocks.Block, rmcids map[cid.Cid]bool) ([]byte, error)
}

// func blocksToCar(root cid.Cid, blks map[cid.Cid]blocks.Block) ([]byte, error) {
// 	buf := new(bytes.Buffer)
// 	_, err := WriteCarHeader(buf, root)
// 	if err != nil {
// 		return nil, fmt.Errorf("failed to write car header: %w", err)
// 	}
//
// 	for k, blk := range blks {
// 		_, err := LdWrite(buf, k.Bytes(), blk.RawData())
// 		if err != nil {
// 			return nil, fmt.Errorf("failed to write block: %w", err)
// 		}
// 	}
//
// 	return buf.Bytes(), nil
// }

func (cs *FileCarStore) writeNewShard(ctx context.Context, root cid.Cid, rev string, user atp.Uid, seq int, blks map[cid.Cid]blocks.Block, rmcids map[cid.Cid]bool) ([]byte, error) {
	buf := new(bytes.Buffer)
	hnw, err := WriteCarHeader(buf, root)
	if err != nil {
		return nil, fmt.Errorf("failed to write car header: %w", err)
	}

	// TODO: writing these blocks in map traversal order is bad, I believe the
	// optimal ordering will be something like reverse-write-order, but random
	// is definitely not it

	offset := hnw
	//brefs := make([]*blockRef, 0, len(ds.blks))
	var brefs []*BlockRef
	for k, blk := range blks {
		nw, nerr := LdWrite(buf, k.Bytes(), blk.RawData())
		if nerr != nil {
			return nil, fmt.Errorf("failed to write block: %w", err)
		}

		brefs = append(brefs, &BlockRef{
			Cid:        atp.DbCID{CID: k},
			ByteOffset: offset,
			Uid:        user,
		})

		offset += nw
	}

	start := time.Now()
	path, err := cs.writeNewShardFile(ctx, user, seq, buf.Bytes())
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
	if err := cs.putShard(ctx, &shard, brefs, rmcids, false); err != nil {
		return nil, err
	}
	writeShardMetadataDuration.Observe(time.Since(start).Seconds())

	return buf.Bytes(), nil
}

func (cs *FileCarStore) putShard(ctx context.Context, shard *Shard, brefs []*BlockRef, rmcids map[cid.Cid]bool, nocache bool) error {
	ctx, span := otel.Tracer("carstore").Start(ctx, "putShard")
	defer span.End()

	err := cs.meta.PutShardAndRefs(ctx, shard, brefs, rmcids)
	if err != nil {
		return err
	}

	if !nocache {
		cs.putLastShardCache(shard)
	}

	return nil
}

func BlockDiff(ctx context.Context, bs blockstore.Blockstore, oldroot cid.Cid, newcids map[cid.Cid]blocks.Block, skipcids map[cid.Cid]bool) (map[cid.Cid]bool, error) {
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
		return nil, nil
	}

	// next, walk the old tree from the root, recursing on cids *not* in the keepset.
	dropset := make(map[cid.Cid]bool)
	dropset[oldroot] = true
	queue := []cid.Cid{oldroot}

	for len(queue) > 0 {
		c := queue[0]
		queue = queue[1:]

		if skipcids != nil && skipcids[c] {
			continue
		}

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

func (cs *FileCarStore) ImportSlice(ctx context.Context, uid atp.Uid, since *string, carslice []byte) (cid.Cid, *DeltaSession, error) {
	ctx, span := otel.Tracer("carstore").Start(ctx, "ImportSlice")
	defer span.End()

	carr, err := car.NewCarReader(bytes.NewReader(carslice))
	if err != nil {
		return cid.Undef, nil, err
	}

	if len(carr.Header.Roots) != 1 {
		return cid.Undef, nil, fmt.Errorf("invalid car file, header must have a single root (has %d)", len(carr.Header.Roots))
	}

	ds, err := cs.NewDeltaSession(ctx, uid, since)
	if err != nil {
		return cid.Undef, nil, fmt.Errorf("new delta session failed: %w", err)
	}

	for {
		blk, err := carr.Next()
		if err != nil {
			if err == io.EOF {
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

func (ds *DeltaSession) CalcDiff(ctx context.Context, skipcids map[cid.Cid]bool) error {
	rmcids, err := BlockDiff(ctx, ds, ds.baseCid, ds.blks, skipcids)
	if err != nil {
		return fmt.Errorf("block diff failed (base=%s,rev=%s): %w", ds.baseCid, ds.lastRev, err)
	}

	ds.rmcids = rmcids
	return nil
}

func (cs *FileCarStore) GetUserRepoHead(ctx context.Context, user atp.Uid) (cid.Cid, error) {
	lastShard, err := cs.getLastShard(ctx, user)
	if err != nil {
		return cid.Undef, err
	}
	if lastShard.ID == 0 {
		return cid.Undef, nil
	}

	return lastShard.Root.CID, nil
}

func (cs *FileCarStore) GetUserRepoRev(ctx context.Context, user atp.Uid) (string, error) {
	lastShard, err := cs.getLastShard(ctx, user)
	if err != nil {
		return "", err
	}
	if lastShard.ID == 0 {
		return "", nil
	}

	fmt.Printf("GetUserRepoRev: Rev=[%s], ID=%d, len(Rev)=%d\n",
		lastShard.Rev, lastShard.ID, len(lastShard.Rev))

	// Examine each byte if necessary
	if len(lastShard.Rev) > 0 {
		fmt.Printf("Rev bytes: %v\n", []byte(lastShard.Rev))
	}
	return lastShard.Rev, nil
}

type UserStat struct {
	Seq     int
	Root    string
	Created time.Time
}

func (cs *FileCarStore) Stat(ctx context.Context, usr atp.Uid) ([]UserStat, error) {
	shards, err := cs.meta.GetUserShards(ctx, usr)
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

func (cs *FileCarStore) WipeUserData(ctx context.Context, user atp.Uid) error {
	shards, err := cs.meta.GetUserShards(ctx, user)
	if err != nil {
		return err
	}

	if err := cs.deleteShards(ctx, shards); err != nil {
		if !os.IsNotExist(err) {
			return err
		}
	}

	cs.removeLastShardCache(user)

	return nil
}

func (cs *FileCarStore) deleteShards(ctx context.Context, shs []*Shard) error {
	ctx, span := otel.Tracer("carstore").Start(ctx, "deleteShards")
	defer span.End()

	deleteSlice := func(ctx context.Context, subs []*Shard) error {
		ids := make([]uint, len(subs))
		for i, sh := range subs {
			ids[i] = sh.ID
		}

		err := cs.meta.DeleteShardsAndRefs(ctx, ids)
		if err != nil {
			return err
		}

		for _, sh := range subs {
			if err := cs.deleteShardFile(sh); err != nil {
				if !os.IsNotExist(err) {
					return err
				}
				cs.log.Warn("shard file we tried to delete did not exist", "shard", sh.ID, "path", sh.Path)
			}
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

func aggrRefs(brefs []*BlockRef, shards map[uint]*Shard, staleCids map[cid.Cid]bool) []shardStat {
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
		if staleCids[br.Cid.CID] {
			s.Dirty++
		}

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

func (cs *FileCarStore) openNewCompactedShardFile(user atp.Uid, seq int) (*os.File, string, error) {
	// TODO: some overwrite protections
	// NOTE CreateTemp is used for creating a non-colliding file, but we keep it and don't delete it so don't think of it as "temporary".
	// This creates "sh-%d-%d%s" with some random stuff in the last position
	fi, err := os.CreateTemp(cs.dirForUser(user), fnameForShard(user, seq))
	if err != nil {
		return nil, "", err
	}

	return fi, fi.Name(), nil
}

type CompactionTarget struct {
	Usr       atp.Uid `db:"uid"`
	NumShards int     `db:"num_shards"`
}

func (t CompactionTarget) TableName() string {
	return "car_shards"
}

func (cs *FileCarStore) GetCompactionTargets(ctx context.Context, shardCount int) ([]*CompactionTarget, error) {
	ctx, span := otel.Tracer("carstore").Start(ctx, "GetCompactionTargets")
	defer span.End()

	return cs.meta.GetCompactionTargets(ctx, shardCount)
}

// getBlockRefsForShards is a prep function for CompactUserShards
func (cs *FileCarStore) getBlockRefsForShards(ctx context.Context, shardIds []uint) ([]*BlockRef, error) {
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

func shardSize(sh *Shard) (int64, error) {
	st, err := os.Stat(sh.Path)
	if err != nil {
		if os.IsNotExist(err) {
			slog.Warn("missing shard, return size of zero", "path", sh.Path, "shard", sh.ID, "system", "carstore")
			return 0, nil
		}
		return 0, fmt.Errorf("stat %q: %w", sh.Path, err)
	}

	return st.Size(), nil
}

type CompactionStats struct {
	TotalRefs     int `json:"totalRefs"`
	StartShards   int `json:"startShards"`
	NewShards     int `json:"newShards"`
	SkippedShards int `json:"skippedShards"`
	ShardsDeleted int `json:"shardsDeleted"`
	DupeCount     int `json:"dupeCount"`
}

func (cs *FileCarStore) CompactUserShards(ctx context.Context, user atp.Uid, skipBigShards bool) (*CompactionStats, error) {
	ctx, span := otel.Tracer("carstore").Start(ctx, "CompactUserShards")
	defer span.End()

	span.SetAttributes(attribute.Int64("user", int64(uint64(user)))) // nolint:gosec

	shards, err := cs.meta.GetUserShards(ctx, user)
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
			size, serr := shardSize(sh)
			if serr != nil {
				return nil, fmt.Errorf("could not check size of shard file: %w", err)
			}

			if size > BigShardThreshold {
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

	staleRefs, err := cs.meta.GetUserStaleRefs(ctx, user)
	if err != nil {
		return nil, err
	}

	span.SetAttributes(attribute.Int("staleRefs", len(staleRefs)))

	stale := make(map[cid.Cid]bool)
	for _, br := range staleRefs {
		cids, err := br.getCids()
		if err != nil {
			return nil, fmt.Errorf("failed to unpack cids from staleRefs record (%d): %w", br.ID, err)
		}
		for _, c := range cids {
			stale[c] = true
		}
	}

	// if we have a staleRef that references multiple blockRefs, we consider that block a 'dirty duplicate'
	var dupes []cid.Cid
	var hasDirtyDupes bool
	seenBlocks := make(map[cid.Cid]bool)
	for _, br := range brefs {
		if seenBlocks[br.Cid.CID] {
			dupes = append(dupes, br.Cid.CID)
			hasDirtyDupes = true
			delete(stale, br.Cid.CID)
		} else {
			seenBlocks[br.Cid.CID] = true
		}
	}

	for _, dupe := range dupes {
		delete(stale, dupe) // remove dupes from stale list, see comment below
	}

	if hasDirtyDupes {
		// if we have no duplicates, then the keep set is simply all the 'clean' blockRefs
		// in the case we have duplicate dirty references we have to compute
		// the keep set by walking the entire repo to check if anything is
		// still referencing the dirty block in question

		// we could also just add the duplicates to the keep set for now and
		// focus on compacting everything else. it leaves *some* dirty blocks
		// still around but we're doing that anyways since compaction isn't a
		// perfect process

		cs.log.Debug("repo has dirty dupes", "count", len(dupes), "uid", user, "staleRefs", len(staleRefs), "blockRefs", len(brefs))

		//return nil, fmt.Errorf("WIP: not currently handling this case")
	}

	keep := make(map[cid.Cid]bool)
	for _, br := range brefs {
		if !stale[br.Cid.CID] {
			keep[br.Cid.CID] = true
		}
	}

	for _, dupe := range dupes {
		keep[dupe] = true
	}

	results := aggrRefs(brefs, shardsById, stale)
	var sum int
	for _, r := range results {
		sum += r.Total
	}

	lowBound := 20
	N := 10
	// we want to *aim* for N shards per user
	// the last several should be left small to allow easy loading from disk
	// for updates (since recent blocks are most likely needed for edits)
	// the beginning of the list should be some sort of exponential fall-off
	// with the area under the curve targeted by the total number of blocks we
	// have
	var threshs []int
	tot := len(brefs)
	for range make([]struct{}, N) {
		v := max(tot/2, lowBound)
		tot = tot / 2
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

		if err := cs.compactBucket(ctx, user, b, shardsById, keep); err != nil {
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
		if err := cs.deleteShards(ctx, todelete); err != nil {
			return nil, fmt.Errorf("deleting shards: %w", err)
		}
	}

	// now we need to delete the staleRefs we successfully cleaned up
	// we can safely delete a staleRef if all the shards that have blockRefs with matching stale refs were processed
	if err := cs.deleteStaleRefs(ctx, user, brefs, staleRefs, removedShards); err != nil {
		return nil, fmt.Errorf("delete stale refs: %w", err)
	}

	stats.DupeCount = len(dupes)

	return stats, nil
}

func (cs *FileCarStore) deleteStaleRefs(ctx context.Context, uid atp.Uid, brefs []*BlockRef, staleRefs []*StaleRef, removedShards map[uint]bool) error {
	ctx, span := otel.Tracer("carstore").Start(ctx, "deleteStaleRefs")
	defer span.End()

	brByCid := make(map[cid.Cid][]*BlockRef)
	for _, br := range brefs {
		brByCid[br.Cid.CID] = append(brByCid[br.Cid.CID], br)
	}

	var staleToKeep []cid.Cid
	for _, sr := range staleRefs {
		cids, err := sr.getCids()
		if err != nil {
			return fmt.Errorf("getCids on staleRef failed (%d): %w", sr.ID, err)
		}

		for _, c := range cids {
			brs := brByCid[c]
			del := true
			for _, br := range brs {
				if !removedShards[br.Shard] {
					del = false
					break
				}
			}

			if !del {
				staleToKeep = append(staleToKeep, c)
			}
		}
	}

	return cs.meta.SetStaleRef(ctx, uid, staleToKeep)
}

func (cs *FileCarStore) compactBucket(ctx context.Context, user atp.Uid, b *compBucket, shardsById map[uint]*Shard, keep map[cid.Cid]bool) error {
	ctx, span := otel.Tracer("carstore").Start(ctx, "compactBucket")
	defer span.End()

	span.SetAttributes(attribute.Int("shards", len(b.shards)))

	last := b.shards[len(b.shards)-1]
	lastsh := shardsById[last.ID]
	fi, path, err := cs.openNewCompactedShardFile(user, last.Seq)
	if err != nil {
		return fmt.Errorf("opening new file: %w", err)
	}

	defer fi.Close()
	root := lastsh.Root.CID

	hnw, err := WriteCarHeader(fi, root)
	if err != nil {
		return err
	}

	offset := hnw
	var nbrefs []*BlockRef
	written := make(map[cid.Cid]bool)
	for _, s := range b.shards {
		sh := shardsById[s.ID]
		if err := cs.iterateShardBlocks(sh, func(blk blocks.Block) error {
			if written[blk.Cid()] {
				return nil
			}

			if keep[blk.Cid()] {
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
			}
			return nil
		}); err != nil {
			// If we ever fail to iterate a shard file because its
			// corrupted, just log an error and skip the shard
			cs.log.Error("iterating blocks in shard", "shard", s.ID, "err", err, "uid", user)
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

	if err := cs.putShard(ctx, &shard, nbrefs, nil, true); err != nil {
		// if writing the shard fails, we should also delete the file
		_ = fi.Close()

		if err2 := os.Remove(fi.Name()); err2 != nil {
			cs.log.Error("failed to remove shard file after failed db transaction", "path", fi.Name(), "err", err2)
		}

		return err
	}
	return nil
}
