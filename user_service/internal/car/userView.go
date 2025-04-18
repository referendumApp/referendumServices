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
	HasUidCid(ctx context.Context, user atp.Uid, k cid.Cid) (bool, error)
	LookupBlockRef(ctx context.Context, k cid.Cid) (path string, offset int64, user atp.Uid, err error)
}

// wrapper into a block store that keeps track of which user we are working on behalf of
type userView struct {
	client *s3Client
	cs     userViewSource
	user   atp.Uid

	cache    map[cid.Cid]blocks.Block
	prefetch bool
}

var _ blockstore.Blockstore = (*userView)(nil)

// HashOnRead noop
func (uv *userView) HashOnRead(hor bool) {}

// Has checks cache and DB for a CID
func (uv *userView) Has(ctx context.Context, k cid.Cid) (bool, error) {
	_, have := uv.cache[k]
	if have {
		return have, nil
	}
	return uv.cs.HasUidCid(ctx, uv.user, k)
}

// CacheHits counter for user view cache hits
var CacheHits int64

// CacheMiss counter for user view cache misses
var CacheMiss int64

// Get the blocks for a given CID
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
		return uv.singleRead(ctx, k, path, offset)
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

func (uv *userView) prefetchRead(
	ctx context.Context,
	k cid.Cid,
	path string,
	offset int64,
) (outblk blocks.Block, err error) {
	_, span := otel.Tracer("carstore").Start(ctx, "getLastShard")
	defer span.End()

	obj, err := uv.client.readFile(ctx, path, nil)
	if err != nil {
		return nil, err
	}
	defer func() {
		closeErr := obj.Body.Close()
		if err == nil {
			err = closeErr
		}
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

		uv.cache[blk.Cid()] = blk
	}

	outblk, ok := uv.cache[k]
	if !ok {
		return nil, fmt.Errorf("requested block was not found in car slice")
	}

	return outblk, nil
}

func (uv *userView) singleRead(
	ctx context.Context,
	k cid.Cid,
	path string,
	offset int64,
) (blk blocks.Block, err error) {
	obj, err := uv.client.readFile(ctx, path, &offset)
	if err != nil {
		return nil, err
	}
	defer func() {
		closeErr := obj.Body.Close()
		if err == nil {
			err = closeErr
		}
	}()

	return doBlockRead(obj.Body, k)
}

// AllKeysChan not implemented
func (uv *userView) AllKeysChan(ctx context.Context) (<-chan cid.Cid, error) {
	return nil, fmt.Errorf("not implemented")
}

// Put userView is readonly
func (uv *userView) Put(ctx context.Context, blk blocks.Block) error {
	return fmt.Errorf("puts not supported to car view blockstores")
}

// PutMany userView is readonly
func (uv *userView) PutMany(ctx context.Context, blks []blocks.Block) error {
	return fmt.Errorf("puts not supported to car view blockstores")
}

// DeleteBlock userView is readonly
func (uv *userView) DeleteBlock(ctx context.Context, k cid.Cid) error {
	return fmt.Errorf("deletes not supported to car view blockstore")
}

// GetSize returns block size
func (uv *userView) GetSize(ctx context.Context, k cid.Cid) (int, error) {
	// TODO: maybe block size should be in the database record...
	blk, err := uv.Get(ctx, k)
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
