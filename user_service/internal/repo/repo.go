package repo

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"

	lexutil "github.com/bluesky-social/indigo/lex/util"
	"github.com/bluesky-social/indigo/mst"
	"github.com/bluesky-social/indigo/util"
	blockstore "github.com/ipfs/boxo/blockstore"
	"github.com/ipfs/go-cid"
	"github.com/ipfs/go-datastore"
	cbor "github.com/ipfs/go-ipld-cbor"
	"github.com/ipld/go-car/v2"
	cbg "github.com/whyrusleeping/cbor-gen"
	"go.opentelemetry.io/otel"
)

// ATP_REPO_VERSION current version of repo currently implemented
const ATP_REPO_VERSION int64 = 3

// ATP_REPO_VERSION_2 previous version of the repo
const ATP_REPO_VERSION_2 int64 = 2

// SignedCommit schema for repository commit which is used as the root
type SignedCommit struct {
	Did     string   `json:"did"     cborgen:"did"`
	Version int64    `json:"version" cborgen:"version"`
	Prev    *cid.Cid `json:"prev"    cborgen:"prev"`
	Data    cid.Cid  `json:"data"    cborgen:"data"`
	Sig     []byte   `json:"sig"     cborgen:"sig"`
	Rev     string   `json:"rev"     cborgen:"rev,omitempty"`
}

// UnsignedCommit schema before signing the commit
type UnsignedCommit struct {
	Did     string   `cborgen:"did"`
	Version int64    `cborgen:"version"`
	Prev    *cid.Cid `cborgen:"prev"`
	Data    cid.Cid  `cborgen:"data"`
	Rev     string   `cborgen:"rev,omitempty"`
}

// Repo represents an actor repository and contains all the dependencies repo CRUD operations
type Repo struct {
	sc  SignedCommit
	cst cbor.IpldStore
	bs  cbor.IpldBlockstore

	repoCid cid.Cid

	mst *mst.MerkleSearchTree

	dirty bool
}

// Unsigned returns a copy of commit without the Sig field. Helpful when verifying signature.
func (sc *SignedCommit) Unsigned() *UnsignedCommit {
	return &UnsignedCommit{
		Did:     sc.Did,
		Version: sc.Version,
		Prev:    sc.Prev,
		Data:    sc.Data,
		Rev:     sc.Rev,
	}
}

// BytesForSigning returns bytes of the DAG-CBOR representation of object. This is what gets
// signed; the `go-did` library will take the SHA-256 of the bytes and sign
// that.
func (uc *UnsignedCommit) BytesForSigning() ([]byte, error) {
	buf := new(bytes.Buffer)
	if err := uc.MarshalCBOR(buf); err != nil {
		return []byte{}, err
	}
	return buf.Bytes(), nil
}

// IngestRepo writes an entire CAR file
// TODO: is unused not sure if necessary
func IngestRepo(ctx context.Context, bs cbor.IpldBlockstore, r io.Reader) (cid.Cid, error) {
	ctx, span := otel.Tracer("repo").Start(ctx, "Ingest")
	defer span.End()

	br, err := car.NewBlockReader(r)
	if err != nil {
		return cid.Undef, fmt.Errorf("opening CAR block reader: %w", err)
	}

	for {
		blk, err := br.Next()
		if err != nil {
			if errors.Is(err, io.EOF) {
				break
			}
			return cid.Undef, fmt.Errorf("reading block from CAR: %w", err)
		}

		if err := bs.Put(ctx, blk); err != nil {
			return cid.Undef, fmt.Errorf("copying block to store: %w", err)
		}
	}

	return br.Roots[0], nil
}

// ReadRepoFromCar takes a CAR file and writes it somewhere else
// TODO: is unused not sure if necessary
func ReadRepoFromCar(ctx context.Context, r io.Reader) (*Repo, error) {
	bs := blockstore.NewBlockstore(datastore.NewMapDatastore())
	root, err := IngestRepo(ctx, bs, r)
	if err != nil {
		return nil, fmt.Errorf("ReadRepoFromCar:IngestRepo: %w", err)
	}

	return OpenRepo(ctx, bs, root)
}

// NewRepo initializes an empty 'Repo' struct instance
func NewRepo(ctx context.Context, did string, bs cbor.IpldBlockstore) *Repo {
	cst := util.CborStore(bs)

	t := mst.NewEmptyMST(cst)
	sc := SignedCommit{
		Did:     did,
		Version: 2,
	}

	return &Repo{
		cst:   cst,
		bs:    bs,
		mst:   t,
		sc:    sc,
		dirty: true,
	}
}

// OpenRepo initializes a 'Repo' struct with the root commit for the session
func OpenRepo(ctx context.Context, bs cbor.IpldBlockstore, root cid.Cid) (*Repo, error) {
	cst := util.CborStore(bs)

	var sc SignedCommit
	if err := cst.Get(ctx, root, &sc); err != nil {
		return nil, fmt.Errorf("loading root from blockstore: %w", err)
	}

	if sc.Version != ATP_REPO_VERSION && sc.Version != ATP_REPO_VERSION_2 {
		return nil, fmt.Errorf("unsupported repo version: %d", sc.Version)
	}

	return &Repo{
		sc:      sc,
		bs:      bs,
		cst:     cst,
		repoCid: root,
	}, nil
}

// RepoDid returns the DID for the repo instance
func (r *Repo) RepoDid() string {
	if r.sc.Did == "" {
		panic("repo has unset did")
	}

	return r.sc.Did
}

// PrevCommit returns the previous signed commit (prev is deprecated in v3)
func (r *Repo) PrevCommit(ctx context.Context) *cid.Cid {
	return r.sc.Prev
}

// DataCid returns the CID containing the node data
func (r *Repo) DataCid() cid.Cid {
	return r.sc.Data
}

// SignedCommit returns the signed commit
func (r *Repo) SignedCommit() SignedCommit {
	return r.sc
}

// Blockstore returns the block store (DeltaSession)
func (r *Repo) Blockstore() cbor.IpldBlockstore {
	return r.bs
}

// CreateRecord writes the record as a node (NodeData) in the MST
func (r *Repo) CreateRecord(ctx context.Context, rpath string, rec cbg.CBORMarshaler) (cid.Cid, error) {
	ctx, span := otel.Tracer("repo").Start(ctx, "CreateRecord")
	defer span.End()

	r.dirty = true
	t, err := r.getMst(ctx)
	if err != nil {
		return cid.Undef, fmt.Errorf("failed to get mst: %w", err)
	}

	k, err := r.cst.Put(ctx, rec)
	if err != nil {
		return cid.Undef, err
	}

	nmst, err := t.Add(ctx, rpath, k, -1)
	if err != nil {
		return cid.Undef, fmt.Errorf("mst.Add failed: %w", err)
	}

	r.mst = nmst
	return k, nil
}

// UpdateRecord updates an existing entry in the MST
func (r *Repo) UpdateRecord(ctx context.Context, rpath string, rec cbg.CBORMarshaler) (cid.Cid, error) {
	ctx, span := otel.Tracer("repo").Start(ctx, "UpdateRecord")
	defer span.End()

	r.dirty = true
	t, err := r.getMst(ctx)
	if err != nil {
		return cid.Undef, fmt.Errorf("failed to get mst: %w", err)
	}

	k, err := r.cst.Put(ctx, rec)
	if err != nil {
		return cid.Undef, err
	}

	nmst, err := t.Update(ctx, rpath, k)
	if err != nil {
		return cid.Undef, fmt.Errorf("mst.Add failed: %w", err)
	}

	r.mst = nmst
	return k, nil
}

// DeleteRecord deletes an entry in the MST
func (r *Repo) DeleteRecord(ctx context.Context, rpath string) error {
	ctx, span := otel.Tracer("repo").Start(ctx, "DeleteRecord")
	defer span.End()

	r.dirty = true
	t, err := r.getMst(ctx)
	if err != nil {
		return fmt.Errorf("failed to get mst: %w", err)
	}

	nmst, err := t.Delete(ctx, rpath)
	if err != nil {
		return fmt.Errorf("mst.Add failed: %w", err)
	}

	r.mst = nmst
	return nil
}

// Truncate truncates history while retaining the same data root
func (r *Repo) Truncate() {
	r.sc.Prev = nil
	r.repoCid = cid.Undef
}

// Commit creates and writes a new SignedCommit for this repo which will be the new root
func (r *Repo) Commit(
	ctx context.Context,
	signer func(context.Context, string, []byte) ([]byte, error),
) (cid.Cid, string, error) {
	ctx, span := otel.Tracer("repo").Start(ctx, "Commit")
	defer span.End()

	t, err := r.getMst(ctx)
	if err != nil {
		return cid.Undef, "", err
	}

	rcid, err := t.GetPointer(ctx)
	if err != nil {
		return cid.Undef, "", err
	}

	ncom := UnsignedCommit{
		Did:     r.RepoDid(),
		Version: ATP_REPO_VERSION,
		Data:    rcid,
		Rev:     NextTID(),
	}

	sb, err := ncom.BytesForSigning()
	if err != nil {
		return cid.Undef, "", fmt.Errorf("failed to serialize commit: %w", err)
	}
	sig, err := signer(ctx, ncom.Did, sb)
	if err != nil {
		return cid.Undef, "", fmt.Errorf("failed to sign root: %w", err)
	}

	nsc := SignedCommit{
		Sig:     sig,
		Did:     ncom.Did,
		Version: ncom.Version,
		Prev:    ncom.Prev,
		Data:    ncom.Data,
		Rev:     ncom.Rev,
	}

	nsccid, err := r.cst.Put(ctx, &nsc)
	if err != nil {
		return cid.Undef, "", err
	}

	r.sc = nsc
	r.dirty = false

	return nsccid, nsc.Rev, nil
}

func (r *Repo) getMst(ctx context.Context) (*mst.MerkleSearchTree, error) {
	if r.mst != nil {
		return r.mst, nil
	}

	t := mst.LoadMST(r.cst, r.sc.Data)
	r.mst = t
	return t, nil
}

// ErrDoneIterating no more leaves
var ErrDoneIterating = fmt.Errorf("done iterating")

// ForEach execute callback function for each leaf in the tree
func (r *Repo) ForEach(ctx context.Context, prefix string, cb func(k string, v cid.Cid) error) error {
	ctx, span := otel.Tracer("repo").Start(ctx, "ForEach")
	defer span.End()

	t := mst.LoadMST(r.cst, r.sc.Data)

	if err := t.WalkLeavesFrom(ctx, prefix, cb); err != nil {
		if !errors.Is(err, ErrDoneIterating) {
			return err
		}
	}

	return nil
}

// GetRecord reads the block from the record path into the 'rec' struct
func (r *Repo) GetRecord(ctx context.Context, rpath string, rec cbg.CBORMarshaler) (cid.Cid, error) {
	ctx, span := otel.Tracer("repo").Start(ctx, "GetRecord")
	defer span.End()

	cc, recB, err := r.GetRecordBytes(ctx, rpath)
	if err != nil {
		return cid.Undef, err
	}

	if recB == nil {
		return cid.Undef, fmt.Errorf("empty record bytes")
	}

	if err := cbor.DecodeInto(*recB, rec); err != nil {
		return cid.Undef, err
	}

	return cc, nil
}

// GetEventRecord reads the block from the record path and returns the record
func (r *Repo) GetEventRecord(ctx context.Context, rpath string) (cid.Cid, cbg.CBORMarshaler, error) {
	ctx, span := otel.Tracer("repo").Start(ctx, "GetRecord")
	defer span.End()

	cc, recB, err := r.GetRecordBytes(ctx, rpath)
	if err != nil {
		return cid.Undef, nil, err
	}

	if recB == nil {
		return cid.Undef, nil, fmt.Errorf("empty record bytes")
	}

	rec, err := lexutil.CborDecodeValue(*recB)
	if err != nil {
		return cid.Undef, nil, err
	}

	return cc, rec, nil
}

// GetRecordBytes returns the CID and the slice of bytes for the requested record
func (r *Repo) GetRecordBytes(ctx context.Context, rpath string) (cid.Cid, *[]byte, error) {
	ctx, span := otel.Tracer("repo").Start(ctx, "GetRecordBytes")
	defer span.End()

	mst, err := r.getMst(ctx)
	if err != nil {
		return cid.Undef, nil, fmt.Errorf("getting repo mst: %w", err)
	}

	cc, err := mst.Get(ctx, rpath)
	if err != nil {
		return cid.Undef, nil, fmt.Errorf("resolving rpath within mst: %w", err)
	}

	blk, err := r.bs.Get(ctx, cc)
	if err != nil {
		return cid.Undef, nil, err
	}

	raw := blk.RawData()

	return cc, &raw, nil
}

// DiffSince returns the diff between two instances of the MST
func (r *Repo) DiffSince(ctx context.Context, oldrepo cid.Cid) ([]*mst.DiffOp, error) {
	ctx, span := otel.Tracer("repo").Start(ctx, "DiffSince")
	defer span.End()

	var oldTree cid.Cid
	if oldrepo.Defined() {
		otherRepo, err := OpenRepo(ctx, r.bs, oldrepo)
		if err != nil {
			return nil, err
		}

		oldmst, err := otherRepo.getMst(ctx)
		if err != nil {
			return nil, err
		}

		oldptr, err := oldmst.GetPointer(ctx)
		if err != nil {
			return nil, err
		}
		oldTree = oldptr
	}

	curmst, err := r.getMst(ctx)
	if err != nil {
		return nil, err
	}

	curptr, err := curmst.GetPointer(ctx)
	if err != nil {
		return nil, err
	}

	return mst.DiffTrees(ctx, r.bs, oldTree, curptr)
}

// CopyDataTo copies the blocks into an instance of the block store (DeltaSession)
func (r *Repo) CopyDataTo(ctx context.Context, bs cbor.IpldBlockstore) error {
	return copyRecCbor(ctx, r.bs, bs, r.sc.Data, make(map[cid.Cid]struct{}))
}

func copyRecCbor(ctx context.Context, from, to cbor.IpldBlockstore, c cid.Cid, seen map[cid.Cid]struct{}) error {
	if _, ok := seen[c]; ok {
		return nil
	}
	seen[c] = struct{}{}

	blk, err := from.Get(ctx, c)
	if err != nil {
		return err
	}

	if err := to.Put(ctx, blk); err != nil {
		return err
	}

	var out []cid.Cid
	if err := cbg.ScanForLinks(bytes.NewReader(blk.RawData()), func(c cid.Cid) {
		out = append(out, c)
	}); err != nil {
		return err
	}

	for _, child := range out {
		if err := copyRecCbor(ctx, from, to, child, seen); err != nil {
			return err
		}
	}

	return nil
}
