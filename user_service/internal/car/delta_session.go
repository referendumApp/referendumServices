package car

import (
	"context"
	"fmt"

	blockstore "github.com/ipfs/boxo/blockstore"
	blocks "github.com/ipfs/go-block-format"
	"github.com/ipfs/go-cid"
	ipld "github.com/ipfs/go-ipld-format"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	"go.opentelemetry.io/otel"
)

// subset of blockstore.Blockstore that we actually use here
type minBlockstore interface {
	Get(ctx context.Context, bcid cid.Cid) (blocks.Block, error)
	Has(ctx context.Context, bcid cid.Cid) (bool, error)
	GetSize(ctx context.Context, bcid cid.Cid) (int, error)
}

// DeltaSession acts as a cache and provides metadata when generating an instance of a repository and MST
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

var _ blockstore.Blockstore = (*DeltaSession)(nil)

// BaseCid returns root CID
func (ds *DeltaSession) BaseCid() cid.Cid {
	return ds.baseCid
}

// Put writes to the in memory blocks map
func (ds *DeltaSession) Put(ctx context.Context, b blocks.Block) error {
	if ds.readonly {
		return fmt.Errorf("cannot write to readonly deltaSession")
	}
	ds.blks[b.Cid()] = b
	return nil
}

// PutMany writes multiple blocks to the in memory blocks map
func (ds *DeltaSession) PutMany(ctx context.Context, bs []blocks.Block) error {
	if ds.readonly {
		return fmt.Errorf("cannot write to readonly deltaSession")
	}

	for _, b := range bs {
		ds.blks[b.Cid()] = b
	}
	return nil
}

// AllKeysChan not implemented
func (ds *DeltaSession) AllKeysChan(ctx context.Context) (<-chan cid.Cid, error) {
	return nil, fmt.Errorf("AllKeysChan not implemented")
}

// DeleteBlock delete block from in memory map
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

// Get block from in memory cache or DB
func (ds *DeltaSession) Get(ctx context.Context, c cid.Cid) (blocks.Block, error) {
	b, ok := ds.blks[c]
	if ok {
		return b, nil
	}

	return ds.base.Get(ctx, c)
}

// Has in memory cache or DB for CID
func (ds *DeltaSession) Has(ctx context.Context, c cid.Cid) (bool, error) {
	_, ok := ds.blks[c]
	if ok {
		return true, nil
	}

	return ds.base.Has(ctx, c)
}

// HashOnRead noop?
func (ds *DeltaSession) HashOnRead(hor bool) {}

// GetSize returns block size from in memory cache or DB
func (ds *DeltaSession) GetSize(ctx context.Context, c cid.Cid) (int, error) {
	b, ok := ds.blks[c]
	if ok {
		return len(b.RawData()), nil
	}

	return ds.base.GetSize(ctx, c)
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
