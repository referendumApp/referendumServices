package car

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"sync/atomic"

	blockstore "github.com/ipfs/boxo/blockstore"
	blocks "github.com/ipfs/go-block-format"
	"github.com/ipfs/go-cid"
	ipld "github.com/ipfs/go-ipld-format"
	car "github.com/ipld/go-car"
	carutil "github.com/ipld/go-car/util"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
)

var blockGetTotalCounter = promauto.NewCounterVec(prometheus.CounterOpts{
	Name: "carstore_block_get_total",
	Help: "carstore get queries",
}, []string{"usrskip", "cache"})

var blockGetTotalCounterUsrskip = blockGetTotalCounter.WithLabelValues("true", "miss")
var blockGetTotalCounterCached = blockGetTotalCounter.WithLabelValues("false", "hit")
var blockGetTotalCounterNormal = blockGetTotalCounter.WithLabelValues("false", "miss")

// userView needs these things to get into the underlying block store
// implemented by StoreMeta
type userViewSource interface {
	HasAidCid(ctx context.Context, user atp.Aid, k cid.Cid) (bool, error)
	LookupBlockRef(ctx context.Context, k cid.Cid) (path string, offset int64, user atp.Aid, err error)
}

// wrapper into a block store that keeps track of which actor we are working on behalf of
type actorView struct {
	client *s3Client
	cs     userViewSource
	actor  atp.Aid

	cache    map[cid.Cid]blocks.Block
	prefetch bool
}

var _ blockstore.Blockstore = (*actorView)(nil)

// HashOnRead noop
func (av *actorView) HashOnRead(hor bool) {}

// Has checks cache and DB for a CID
func (av *actorView) Has(ctx context.Context, k cid.Cid) (bool, error) {
	_, have := av.cache[k]
	if have {
		return have, nil
	}
	return av.cs.HasAidCid(ctx, av.actor, k)
}

// CacheHits counter for user view cache hits
var CacheHits int64

// CacheMiss counter for user view cache misses
var CacheMiss int64

// Get the blocks for a given CID
func (av *actorView) Get(ctx context.Context, k cid.Cid) (blocks.Block, error) {
	if !k.Defined() {
		return nil, fmt.Errorf("attempted to 'get' undefined cid")
	}
	if av.cache != nil {
		blk, ok := av.cache[k]
		if ok {
			blockGetTotalCounterCached.Add(1)
			atomic.AddInt64(&CacheHits, 1)

			return blk, nil
		}
	}
	atomic.AddInt64(&CacheMiss, 1)

	path, offset, actor, err := av.cs.LookupBlockRef(ctx, k)
	if err != nil {
		return nil, err
	}
	if path == "" {
		return nil, ipld.ErrNotFound{Cid: k}
	}

	prefetch := av.prefetch
	if actor != av.actor {
		blockGetTotalCounterUsrskip.Add(1)
		prefetch = false
	} else {
		blockGetTotalCounterNormal.Add(1)
	}

	if prefetch {
		return av.prefetchRead(ctx, k, path, offset)
	} else {
		return av.singleRead(ctx, k, path, offset)
	}
}

func doBlockRead(fi io.ReadCloser, k cid.Cid) (blocks.Block, error) {
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

func offsetBytes(r io.ReadCloser, offset int64) error {
	if seeker, ok := r.(io.Seeker); ok {
		_, err := seeker.Seek(offset, io.SeekStart)
		return err
	}

	buf := make([]byte, 8192)
	var skipped int64 = 0
	for skipped < offset {
		toSkip := min(int64(len(buf)), offset-skipped)
		n, err := r.Read(buf[:toSkip])
		skipped := int64(n)

		if err != nil {
			if errors.Is(err, io.EOF) && skipped == offset {
				return nil
			}
			return err
		}
	}

	return nil
}

const prefetchThreshold = 512 << 10

func (av *actorView) prefetchRead(
	ctx context.Context,
	k cid.Cid,
	path string,
	offset int64,
) (blocks.Block, error) {
	_, span := otel.Tracer("carstore").Start(ctx, "getLastShard")
	defer span.End()

	obj, err := av.client.readFile(ctx, path, nil)
	if err != nil {
		return nil, err
	}
	defer func() {
		_ = obj.Body.Close()
	}()
	size := *obj.ContentLength

	span.SetAttributes(attribute.Int64("shard_size", size))

	if size > prefetchThreshold {
		span.SetAttributes(attribute.Bool("no_prefetch", true))
		if oerr := offsetBytes(obj.Body, offset); oerr != nil {
			return nil, oerr
		}
		return doBlockRead(obj.Body, k)
	}

	cr, err := car.NewCarReader(obj.Body)
	if err != nil {
		return nil, err
	}

	for {
		blk, err := cr.Next()
		if err != nil {
			if errors.Is(err, io.EOF) {
				break
			}
			return nil, err
		}

		av.cache[blk.Cid()] = blk
	}

	outblk, ok := av.cache[k]
	if !ok {
		return nil, fmt.Errorf("requested block was not found in car slice")
	}

	return outblk, nil
}

func (av *actorView) singleRead(
	ctx context.Context,
	k cid.Cid,
	path string,
	offset int64,
) (blocks.Block, error) {
	obj, err := av.client.readFile(ctx, path, &offset)
	if err != nil {
		return nil, err
	}
	defer func() {
		_ = obj.Body.Close()
	}()

	return doBlockRead(obj.Body, k)
}

// AllKeysChan not implemented
func (av *actorView) AllKeysChan(ctx context.Context) (<-chan cid.Cid, error) {
	return nil, fmt.Errorf("not implemented")
}

// Put userView is readonly
func (av *actorView) Put(ctx context.Context, blk blocks.Block) error {
	return fmt.Errorf("puts not supported to car view blockstores")
}

// PutMany userView is readonly
func (av *actorView) PutMany(ctx context.Context, blks []blocks.Block) error {
	return fmt.Errorf("puts not supported to car view blockstores")
}

// DeleteBlock userView is readonly
func (av *actorView) DeleteBlock(ctx context.Context, k cid.Cid) error {
	return fmt.Errorf("deletes not supported to car view blockstore")
}

// GetSize returns block size
func (av *actorView) GetSize(ctx context.Context, k cid.Cid) (int, error) {
	// TODO: maybe block size should be in the database record...
	blk, err := av.Get(ctx, k)
	if err != nil {
		return 0, err
	}

	return len(blk.RawData()), nil
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
