package repo

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"strings"
	"sync"
	"time"

	atproto "github.com/bluesky-social/indigo/api/atproto"
	lexutil "github.com/bluesky-social/indigo/lex/util"
	"github.com/bluesky-social/indigo/mst"
	"github.com/bluesky-social/indigo/util"
	blockstore "github.com/ipfs/boxo/blockstore"
	blocks "github.com/ipfs/go-block-format"
	"github.com/ipfs/go-cid"
	"github.com/ipfs/go-datastore"
	ipld "github.com/ipfs/go-ipld-format"
	"github.com/ipld/go-car"
	cs "github.com/referendumApp/referendumServices/internal/car"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	cbg "github.com/whyrusleeping/cbor-gen"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
)

// NewRepoManager initializes 'Manager' struct
func NewRepoManager(cs cs.Store, kmgr KeyManager, logger *slog.Logger) *Manager {
	return &Manager{
		cs:        cs,
		userLocks: make(map[atp.Aid]*userLock),
		kmgr:      kmgr,
		log:       logger.With("service", "repomgr"),
	}
}

// KeyManager method signatures for handling the signing key
type KeyManager interface {
	VerifyUserSignature(context.Context, string, []byte, []byte) error
	SignForUser(context.Context, string, []byte) ([]byte, error)
}

// SetEventHandler sets the event callback function
func (rm *Manager) SetEventHandler(cb func(context.Context, *Event), hydrateRecords bool) {
	rm.events = cb
	rm.hydrateRecords = hydrateRecords
}

// Manager contains all the dependencies for managing CRUD repo operations
type Manager struct {
	cs   cs.Store
	kmgr KeyManager

	lklk      sync.Mutex
	userLocks map[atp.Aid]*userLock

	events         func(context.Context, *Event)
	hydrateRecords bool

	log *slog.Logger
}

// Event schema for handling and broadcasting events
type Event struct {
	Actor     atp.Aid
	OldRoot   *cid.Cid
	NewRoot   cid.Cid
	Since     *string
	Rev       string
	RepoSlice []byte
	PDS       uint
	Ops       []Op
}

// Op schema containing the data and metadata for event consumers
type Op struct {
	Kind       EventKind
	Collection string
	Rkey       string
	RecCid     *cid.Cid
	Record     any
}

// EventKind type alias for enumerating event types
type EventKind string

// Event types
const (
	EvtKindCreateRecord = EventKind("create")
	EvtKindUpdateRecord = EventKind("update")
	EvtKindDeleteRecord = EventKind("delete")
)

type userLock struct {
	lk    sync.Mutex
	count int
}

func (rm *Manager) lockUser(ctx context.Context, user atp.Aid) func() {
	_, span := otel.Tracer("repoman").Start(ctx, "userLock")
	defer span.End()

	rm.lklk.Lock()

	ulk, ok := rm.userLocks[user]
	if !ok {
		ulk = &userLock{}
		rm.userLocks[user] = ulk
	}

	ulk.count++

	rm.lklk.Unlock()

	ulk.lk.Lock()

	return func() {
		rm.lklk.Lock()

		ulk.lk.Unlock()
		ulk.count--

		if ulk.count == 0 {
			delete(rm.userLocks, user)
		}
		rm.lklk.Unlock()
	}
}

// CarStore returns CAR store instance
func (rm *Manager) CarStore() cs.Store {
	return rm.cs
}

// CreateRecord creates a repo record and broadcasts the event
func (rm *Manager) CreateRecord(
	ctx context.Context,
	actor atp.Aid,
	nsid string,
	key string,
	rec cbg.CBORMarshaler,
) (cid.Cid, string, error) {
	ctx, span := otel.Tracer("repoman").Start(ctx, "CreateRecord")
	defer span.End()

	unlock := rm.lockUser(ctx, actor)
	defer unlock()

	rev, err := rm.cs.GetUserRepoRev(ctx, actor)
	if err != nil {
		return cid.Undef, "", err
	}

	ds, err := rm.cs.NewDeltaSession(ctx, actor, &rev)
	if err != nil {
		return cid.Undef, "", err
	}

	head := ds.BaseCid()

	r, err := OpenRepo(ctx, ds, head)
	if err != nil {
		return cid.Undef, "", err
	}

	cc, err := r.CreateRecord(ctx, nsid+"/"+key, rec)
	if err != nil {
		return cid.Undef, "", err
	}

	nroot, nrev, err := r.Commit(ctx, rm.kmgr.SignForUser)
	if err != nil {
		return cid.Undef, "", err
	}

	rslice, err := ds.CloseWithRoot(ctx, nroot, nrev)
	if err != nil {
		return cid.Undef, "", fmt.Errorf("close with root: %w", err)
	}

	var oldroot *cid.Cid
	if head.Defined() {
		oldroot = &head
	}

	if rm.events != nil {
		rm.events(ctx, &Event{
			Actor:   actor,
			OldRoot: oldroot,
			NewRoot: nroot,
			Rev:     nrev,
			Since:   &rev,
			Ops: []Op{{
				Kind:       EvtKindCreateRecord,
				Collection: nsid,
				Rkey:       key,
				Record:     rec,
				RecCid:     &cc,
			}},
			RepoSlice: rslice,
		})
	}

	return cc, key, nil
}

// UpdateRecord updates a repo record and broadcasts the event
func (rm *Manager) UpdateRecord(
	ctx context.Context,
	actor atp.Aid,
	nsid string,
	key string,
	rec cbg.CBORMarshaler,
) (cid.Cid, error) {
	ctx, span := otel.Tracer("repoman").Start(ctx, "UpdateRecord")
	defer span.End()

	unlock := rm.lockUser(ctx, actor)
	defer unlock()

	rev, err := rm.cs.GetUserRepoRev(ctx, actor)
	if err != nil {
		return cid.Undef, err
	}

	ds, err := rm.cs.NewDeltaSession(ctx, actor, &rev)
	if err != nil {
		return cid.Undef, err
	}

	head := ds.BaseCid()
	r, err := OpenRepo(ctx, ds, head)
	if err != nil {
		return cid.Undef, err
	}

	cc, err := r.UpdateRecord(ctx, nsid+"/"+key, rec)
	if err != nil {
		return cid.Undef, err
	}

	nroot, nrev, err := r.Commit(ctx, rm.kmgr.SignForUser)
	if err != nil {
		return cid.Undef, err
	}

	rslice, err := ds.CloseWithRoot(ctx, nroot, nrev)
	if err != nil {
		return cid.Undef, fmt.Errorf("close with root: %w", err)
	}

	var oldroot *cid.Cid
	if head.Defined() {
		oldroot = &head
	}

	if rm.events != nil {
		op := Op{
			Kind:       EvtKindUpdateRecord,
			Collection: nsid,
			Rkey:       key,
			RecCid:     &cc,
		}

		if rm.hydrateRecords {
			op.Record = rec
		}

		rm.events(ctx, &Event{
			Actor:     actor,
			OldRoot:   oldroot,
			NewRoot:   nroot,
			Rev:       nrev,
			Since:     &rev,
			Ops:       []Op{op},
			RepoSlice: rslice,
		})
	}

	return cc, nil
}

// DeleteRecord deletes a repo record and broadcasts the event
func (rm *Manager) DeleteRecord(ctx context.Context, actor atp.Aid, nsid string, key string) error {
	ctx, span := otel.Tracer("repoman").Start(ctx, "DeleteRecord")
	defer span.End()

	unlock := rm.lockUser(ctx, actor)
	defer unlock()

	rev, err := rm.cs.GetUserRepoRev(ctx, actor)
	if err != nil {
		return err
	}

	ds, err := rm.cs.NewDeltaSession(ctx, actor, &rev)
	if err != nil {
		return err
	}

	head := ds.BaseCid()
	r, err := OpenRepo(ctx, ds, head)
	if err != nil {
		return err
	}

	if derr := r.DeleteRecord(ctx, nsid+"/"+key); derr != nil {
		return derr
	}

	nroot, nrev, err := r.Commit(ctx, rm.kmgr.SignForUser)
	if err != nil {
		return err
	}

	rslice, err := ds.CloseWithRoot(ctx, nroot, nrev)
	if err != nil {
		return fmt.Errorf("close with root: %w", err)
	}

	var oldroot *cid.Cid
	if head.Defined() {
		oldroot = &head
	}

	if rm.events != nil {
		rm.events(ctx, &Event{
			Actor:   actor,
			OldRoot: oldroot,
			NewRoot: nroot,
			Rev:     nrev,
			Since:   &rev,
			Ops: []Op{{
				Kind:       EvtKindDeleteRecord,
				Collection: nsid,
				Rkey:       key,
			}},
			RepoSlice: rslice,
		})
	}

	return nil
}

// InitNewRepo initializes a new repository, writes the first record, and broadcasts the event
func (rm *Manager) InitNewRepo(
	ctx context.Context,
	actor atp.Aid,
	did string,
	nsid string,
	key string,
	prof cbg.CBORMarshaler,
) error {
	unlock := rm.lockUser(ctx, actor)
	defer unlock()

	if did == "" {
		return fmt.Errorf("must specify DID for new actor")
	}

	if actor == 0 {
		return fmt.Errorf("must specify user for new actor")
	}

	ds, err := rm.cs.NewDeltaSession(ctx, actor, nil)
	if err != nil {
		return fmt.Errorf("creating new delta session: %w", err)
	}

	r := NewRepo(ctx, did, ds)

	if _, cerr := r.CreateRecord(ctx, nsid+"/"+key, prof); cerr != nil {
		return fmt.Errorf("setting initial profile: %w", cerr)
	}

	root, nrev, err := r.Commit(ctx, rm.kmgr.SignForUser)
	if err != nil {
		return fmt.Errorf("committing repo for init: %w", err)
	}

	rslice, err := ds.CloseWithRoot(ctx, root, nrev)
	if err != nil {
		return fmt.Errorf("close with root: %w", err)
	}

	if rm.events != nil {
		op := Op{
			Kind:       EvtKindCreateRecord,
			Collection: nsid,
			Rkey:       key,
		}

		if rm.hydrateRecords {
			op.Record = prof
		}

		rm.events(ctx, &Event{
			Actor:     actor,
			NewRoot:   root,
			Rev:       nrev,
			Ops:       []Op{op},
			RepoSlice: rslice,
		})
	}

	return nil
}

// GetRepoRoot gets the root CID for a repo
func (rm *Manager) GetRepoRoot(ctx context.Context, actor atp.Aid) (cid.Cid, error) {
	unlock := rm.lockUser(ctx, actor)
	defer unlock()

	return rm.cs.GetActorRepoHead(ctx, actor)
}

// GetRepoRev gets the root revision for a repo
func (rm *Manager) GetRepoRev(ctx context.Context, actor atp.Aid) (string, error) {
	unlock := rm.lockUser(ctx, actor)
	defer unlock()

	return rm.cs.GetUserRepoRev(ctx, actor)
}

// ReadRepo reads a CAR file for a given revision
// TODO: might be worth having a type alias for revisions
func (rm *Manager) ReadRepo(ctx context.Context, actor atp.Aid, since string, w io.Writer) error {
	return rm.cs.ReadActorCar(ctx, actor, since, w)
}

// GetRecord reads a record into the 'rev' interface
func (rm *Manager) GetRecord(
	ctx context.Context,
	actor atp.Aid,
	nsid string,
	key string,
	rec cbg.CBORMarshaler,
	maybeCid cid.Cid,
) (cid.Cid, error) {
	bs, err := rm.cs.ReadOnlySession(actor)
	if err != nil {
		return cid.Undef, err
	}

	head, err := rm.cs.GetActorRepoHead(ctx, actor)
	if err != nil {
		return cid.Undef, err
	}

	r, err := OpenRepo(ctx, bs, head)
	if err != nil {
		return cid.Undef, err
	}

	ocid, err := r.GetRecord(ctx, nsid+"/"+key, rec)
	if err != nil {
		return cid.Undef, err
	}

	if maybeCid.Defined() && ocid != maybeCid {
		return cid.Undef, fmt.Errorf("record at specified key had different CID than expected")
	}

	return ocid, nil
}

// GetRecordProof gets all the blocks for a repo
func (rm *Manager) GetRecordProof(
	ctx context.Context,
	actor atp.Aid,
	collection string,
	rkey string,
) (cid.Cid, []blocks.Block, error) {
	robs, err := rm.cs.ReadOnlySession(actor)
	if err != nil {
		return cid.Undef, nil, err
	}

	bs := util.NewLoggingBstore(robs)

	head, err := rm.cs.GetActorRepoHead(ctx, actor)
	if err != nil {
		return cid.Undef, nil, err
	}

	r, err := OpenRepo(ctx, bs, head)
	if err != nil {
		return cid.Undef, nil, err
	}

	_, _, err = r.GetRecordBytes(ctx, collection+"/"+rkey)
	if err != nil {
		return cid.Undef, nil, err
	}

	return head, bs.GetLoggedBlocks(), nil
}

// CheckRepoSig validates a repo instance against a DID and verifies the commits signature
func (rm *Manager) CheckRepoSig(ctx context.Context, r *Repo, expdid string) error {
	ctx, span := otel.Tracer("repoman").Start(ctx, "CheckRepoSig")
	defer span.End()

	repoDid := r.RepoDid()
	if expdid != repoDid {
		return fmt.Errorf("DID in repo did not match (%q != %q)", expdid, repoDid)
	}

	scom := r.SignedCommit()

	usc := scom.Unsigned()
	sb, err := usc.BytesForSigning()
	if err != nil {
		return fmt.Errorf("commit serialization failed: %w", err)
	}
	if err := rm.kmgr.VerifyUserSignature(ctx, repoDid, scom.Sig, sb); err != nil {
		return fmt.Errorf("signature check failed (sig: %x) (sb: %x) : %w", scom.Sig, sb, err)
	}

	return nil
}

// HandleExternalUserEvent event handler for users that do not exist in the current PDS
func (rm *Manager) HandleExternalUserEvent(
	ctx context.Context,
	pdsid uint,
	aid atp.Aid,
	did string,
	since *string,
	nrev string,
	carslice []byte,
	ops []*atproto.SyncSubscribeRepos_RepoOp,
) error {
	ctx, span := otel.Tracer("repoman").Start(ctx, "HandleExternalUserEvent")
	defer span.End()

	span.SetAttributes(attribute.Int64("user", int64(uint64(aid)))) //nolint:gosec

	rm.log.DebugContext(ctx, "HandleExternalUserEvent", "pds", pdsid, "aid", aid, "since", since, "nrev", nrev)

	unlock := rm.lockUser(ctx, aid)
	defer unlock()

	start := time.Now()
	root, ds, err := rm.cs.ImportSlice(ctx, aid, since, carslice)
	if err != nil {
		return fmt.Errorf("importing external carslice: %w", err)
	}

	r, err := OpenRepo(ctx, ds, root)
	if err != nil {
		return fmt.Errorf("opening external user repo (%d, root=%s): %w", aid, root, err)
	}

	if rerr := rm.CheckRepoSig(ctx, r, did); rerr != nil {
		return rerr
	}
	openAndSigCheckDuration.Observe(time.Since(start).Seconds())

	start = time.Now()
	if cerr := ds.CalcDiff(ctx); cerr != nil {
		return fmt.Errorf("failed while calculating mst diff (since=%v): %w", since, cerr)
	}
	calcDiffDuration.Observe(time.Since(start).Seconds())

	evtops := make([]Op, 0, len(ops))

	for _, op := range ops {
		parts := strings.SplitN(op.Path, "/", 2)
		if len(parts) != 2 {
			return fmt.Errorf("invalid rpath in mst diff, must have collection and rkey")
		}

		switch EventKind(op.Action) {
		case EvtKindCreateRecord:
			rop := Op{
				Kind:       EvtKindCreateRecord,
				Collection: parts[0],
				Rkey:       parts[1],
				RecCid:     (*cid.Cid)(op.Cid),
			}

			if rm.hydrateRecords {
				_, rec, gerr := r.GetEventRecord(ctx, op.Path)
				if gerr != nil {
					return fmt.Errorf("reading changed record from car slice: %w", gerr)
				}
				rop.Record = rec
			}

			evtops = append(evtops, rop)
		case EvtKindUpdateRecord:
			rop := Op{
				Kind:       EvtKindUpdateRecord,
				Collection: parts[0],
				Rkey:       parts[1],
				RecCid:     (*cid.Cid)(op.Cid),
			}

			if rm.hydrateRecords {
				_, rec, gerr := r.GetEventRecord(ctx, op.Path)
				if gerr != nil {
					return fmt.Errorf("reading changed record from car slice: %w", gerr)
				}

				rop.Record = rec
			}

			evtops = append(evtops, rop)
		case EvtKindDeleteRecord:
			evtops = append(evtops, Op{
				Kind:       EvtKindDeleteRecord,
				Collection: parts[0],
				Rkey:       parts[1],
			})
		default:
			return fmt.Errorf("unrecognized external user event kind: %q", op.Action)
		}
	}

	start = time.Now()
	rslice, err := ds.CloseWithRoot(ctx, root, nrev)
	if err != nil {
		return fmt.Errorf("close with root: %w", err)
	}
	writeCarSliceDuration.Observe(time.Since(start).Seconds())

	if rm.events != nil {
		rm.events(ctx, &Event{
			Actor: aid,
			//OldRoot:   prev,
			NewRoot:   root,
			Rev:       nrev,
			Since:     since,
			Ops:       evtops,
			RepoSlice: rslice,
			PDS:       pdsid,
		})
	}

	return nil
}

// BatchWrite writes a slice of operations as a single commit
func (rm *Manager) BatchWrite(
	ctx context.Context,
	actor atp.Aid,
	writes []*atproto.RepoApplyWrites_Input_Writes_Elem,
) error {
	ctx, span := otel.Tracer("repoman").Start(ctx, "BatchWrite")
	defer span.End()

	unlock := rm.lockUser(ctx, actor)
	defer unlock()

	rev, err := rm.cs.GetUserRepoRev(ctx, actor)
	if err != nil {
		return err
	}

	ds, err := rm.cs.NewDeltaSession(ctx, actor, &rev)
	if err != nil {
		return err
	}

	head := ds.BaseCid()
	r, err := OpenRepo(ctx, ds, head)
	if err != nil {
		return err
	}

	ops := make([]Op, 0, len(writes))
	for _, w := range writes {
		switch {
		case w.RepoApplyWrites_Create != nil:
			c := w.RepoApplyWrites_Create
			var rkey string
			if c.Rkey != nil {
				rkey = *c.Rkey
			} else {
				rkey = NextTID()
			}

			nsid := c.Collection + "/" + rkey
			cc, perr := r.CreateRecord(ctx, nsid, c.Value.Val)
			if perr != nil {
				return perr
			}

			op := Op{
				Kind:       EvtKindCreateRecord,
				Collection: c.Collection,
				Rkey:       rkey,
				RecCid:     &cc,
			}

			if rm.hydrateRecords {
				op.Record = c.Value.Val
			}

			ops = append(ops, op)
		case w.RepoApplyWrites_Update != nil:
			u := w.RepoApplyWrites_Update

			cc, perr := r.UpdateRecord(ctx, u.Collection+"/"+u.Rkey, u.Value.Val)
			if perr != nil {
				return perr
			}

			op := Op{
				Kind:       EvtKindUpdateRecord,
				Collection: u.Collection,
				Rkey:       u.Rkey,
				RecCid:     &cc,
			}

			if rm.hydrateRecords {
				op.Record = u.Value.Val
			}

			ops = append(ops, op)
		case w.RepoApplyWrites_Delete != nil:
			d := w.RepoApplyWrites_Delete

			if derr := r.DeleteRecord(ctx, d.Collection+"/"+d.Rkey); derr != nil {
				return derr
			}

			ops = append(ops, Op{
				Kind:       EvtKindDeleteRecord,
				Collection: d.Collection,
				Rkey:       d.Rkey,
			})
		default:
			return fmt.Errorf("no operation set in write enum")
		}
	}

	nroot, nrev, err := r.Commit(ctx, rm.kmgr.SignForUser)
	if err != nil {
		return err
	}

	rslice, err := ds.CloseWithRoot(ctx, nroot, nrev)
	if err != nil {
		return fmt.Errorf("close with root: %w", err)
	}

	var oldroot *cid.Cid
	if head.Defined() {
		oldroot = &head
	}

	if rm.events != nil {
		rm.events(ctx, &Event{
			Actor:     actor,
			OldRoot:   oldroot,
			NewRoot:   nroot,
			RepoSlice: rslice,
			Rev:       nrev,
			Since:     &rev,
			Ops:       ops,
		})
	}

	return nil
}

// ImportNewRepo initializes a new repo from an external source
func (rm *Manager) ImportNewRepo(ctx context.Context, actor atp.Aid, repoDid string, r io.Reader, rev *string) error {
	ctx, span := otel.Tracer("repoman").Start(ctx, "ImportNewRepo")
	defer span.End()

	unlock := rm.lockUser(ctx, actor)
	defer unlock()

	currev, err := rm.cs.GetUserRepoRev(ctx, actor)
	if err != nil {
		return err
	}

	curhead, err := rm.cs.GetActorRepoHead(ctx, actor)
	if err != nil {
		return err
	}

	if rev != nil && *rev == "" {
		rev = nil
	}
	if rev == nil {
		// if 'rev' is nil, this implies a fresh sync.
		// in this case, ignore any existing blocks we have and treat this like a clean import.
		curhead = cid.Undef
	}

	if rev != nil && *rev != currev {
		// TODO: we could probably just deal with this
		return fmt.Errorf("ImportNewRepo called with incorrect base")
	}

	err = rm.processNewRepo(
		ctx,
		actor,
		r,
		rev,
		func(ctx context.Context, root cid.Cid, finish func(context.Context, string) ([]byte, error), bs blockstore.Blockstore) error {
			r, oerr := OpenRepo(ctx, bs, root)
			if oerr != nil {
				return fmt.Errorf("opening new repo: %w", oerr)
			}

			scom := r.SignedCommit()

			usc := scom.Unsigned()
			sb, berr := usc.BytesForSigning()
			if berr != nil {
				return fmt.Errorf("commit serialization failed: %w", berr)
			}
			if verr := rm.kmgr.VerifyUserSignature(ctx, repoDid, scom.Sig, sb); verr != nil {
				return fmt.Errorf("new user signature check failed: %w", verr)
			}

			diffops, derr := r.DiffSince(ctx, curhead)
			if derr != nil {
				return fmt.Errorf("diff trees (curhead: %s): %w", curhead, derr)
			}

			ops := make([]Op, 0, len(diffops))
			for _, op := range diffops {
				repoOpsImported.Inc()
				out, perr := rm.processOp(ctx, bs, op, rm.hydrateRecords)
				if perr != nil {
					rm.log.ErrorContext(
						ctx,
						"failed to process repo op",
						"err",
						perr,
						"path",
						op.Rpath,
						"repo",
						repoDid,
					)
				}

				if out != nil {
					ops = append(ops, *out)
				}
			}

			slice, ferr := finish(ctx, scom.Rev)
			if ferr != nil {
				return ferr
			}

			if rm.events != nil {
				rm.events(ctx, &Event{
					Actor: actor,
					//OldRoot:   oldroot,
					NewRoot:   root,
					Rev:       scom.Rev,
					Since:     &currev,
					RepoSlice: slice,
					Ops:       ops,
				})
			}

			return nil
		},
	)
	if err != nil {
		return fmt.Errorf("process new repo (current rev: %s): %w", currev, err)
	}

	return nil
}

func (rm *Manager) processOp(
	ctx context.Context,
	bs blockstore.Blockstore,
	op *mst.DiffOp,
	hydrateRecords bool,
) (*Op, error) {
	parts := strings.SplitN(op.Rpath, "/", 2)
	if len(parts) != 2 {
		return nil, fmt.Errorf("repo mst had invalid rpath: %q", op.Rpath)
	}

	switch op.Op {
	case "add", "mut":

		kind := EvtKindCreateRecord
		if op.Op == "mut" {
			kind = EvtKindUpdateRecord
		}

		outop := &Op{
			Kind:       kind,
			Collection: parts[0],
			Rkey:       parts[1],
			RecCid:     &op.NewCid,
		}

		if !hydrateRecords {
			return outop, nil
		}

		blk, err := bs.Get(ctx, op.NewCid)
		if err != nil {
			return nil, err
		}

		rec, err := lexutil.CborDecodeValue(blk.RawData())
		if err != nil {
			if !errors.Is(err, lexutil.ErrUnrecognizedType) {
				return nil, err
			}

			rm.log.WarnContext(ctx, "failed processing repo diff", "err", err)
		} else {
			outop.Record = rec
		}

		return outop, nil
	case "del":
		return &Op{
			Kind:       EvtKindDeleteRecord,
			Collection: parts[0],
			Rkey:       parts[1],
			RecCid:     nil,
		}, nil

	default:
		return nil, fmt.Errorf("diff returned invalid op type: %q", op.Op)
	}
}

func (rm *Manager) processNewRepo(
	ctx context.Context,
	user atp.Aid,
	r io.Reader,
	rev *string,
	cb func(ctx context.Context, root cid.Cid, finish func(context.Context, string) ([]byte, error), bs blockstore.Blockstore) error,
) error {
	ctx, span := otel.Tracer("repoman").Start(ctx, "processNewRepo")
	defer span.End()

	carr, err := car.NewCarReader(r)
	if err != nil {
		return err
	}

	if len(carr.Header.Roots) != 1 {
		return fmt.Errorf("invalid car file, header must have a single root (has %d)", len(carr.Header.Roots))
	}

	membs := blockstore.NewBlockstore(datastore.NewMapDatastore())

	for {
		blk, cerr := carr.Next()
		if cerr != nil {
			if errors.Is(cerr, io.EOF) {
				break
			}
			return cerr
		}

		if perr := membs.Put(ctx, blk); perr != nil {
			return perr
		}
	}

	seen := make(map[cid.Cid]bool)

	root := carr.Header.Roots[0]
	// TODO: if there are blocks that get convergently recreated throughout
	// the repos lifecycle, this will end up erroneously not including
	// them. We should compute the set of blocks needed to read any repo
	// ops that happened in the commit and use that for our 'output' blocks
	cids, err := rm.walkTree(ctx, seen, root, membs, true)
	if err != nil {
		return fmt.Errorf("walkTree: %w", err)
	}

	ds, err := rm.cs.NewDeltaSession(ctx, user, rev)
	if err != nil {
		return fmt.Errorf("opening delta session: %w", err)
	}

	for _, c := range cids {
		blk, err := membs.Get(ctx, c)
		if err != nil {
			return fmt.Errorf("copying walked cids to cs: %w", err)
		}

		if err := ds.Put(ctx, blk); err != nil {
			return err
		}
	}

	finish := func(ctx context.Context, nrev string) ([]byte, error) {
		return ds.CloseWithRoot(ctx, root, nrev)
	}

	if err := cb(ctx, root, finish, ds); err != nil {
		return fmt.Errorf("cb errored root: %s, rev: %s: %w", root, stringOrNil(rev), err)
	}

	return nil
}

func stringOrNil(s *string) string {
	if s == nil {
		return "nil"
	}
	return *s
}

// walkTree returns all cids linked recursively by the root, skipping any cids
// in the 'skip' map, and not erroring on 'not found' if prevMissing is set
func (rm *Manager) walkTree(
	ctx context.Context,
	skip map[cid.Cid]bool,
	root cid.Cid,
	bs blockstore.Blockstore,
	prevMissing bool,
) ([]cid.Cid, error) {
	// TODO: what if someone puts non-cbor links in their repo?
	if root.Prefix().Codec != cid.DagCBOR {
		return nil, fmt.Errorf("can only handle dag-cbor objects in repos (%s is %d)", root, root.Prefix().Codec)
	}

	blk, err := bs.Get(ctx, root)
	if err != nil {
		return nil, err
	}

	var links []cid.Cid
	if err := cbg.ScanForLinks(bytes.NewReader(blk.RawData()), func(c cid.Cid) {
		if c.Prefix().Codec == cid.Raw {
			rm.log.DebugContext(ctx, "skipping 'raw' CID in record", "recordCid", root, "rawCid", c)
			return
		}
		if skip[c] {
			return
		}

		links = append(links, c)
		skip[c] = true
	}); err != nil {
		return nil, err
	}

	out := []cid.Cid{root}
	skip[root] = true

	// TODO: should do this non-recursive since i expect these may get deep
	for _, c := range links {
		sub, err := rm.walkTree(ctx, skip, c, bs, prevMissing)
		if err != nil {
			if prevMissing && !ipld.IsNotFound(err) {
				return nil, err
			}
		}

		out = append(out, sub...)
	}

	return out, nil
}

// TakeDownRepo deletes all CAR files and blocks
func (rm *Manager) TakeDownRepo(ctx context.Context, uid atp.Aid) error {
	unlock := rm.lockUser(ctx, uid)
	defer unlock()

	return rm.cs.WipeUserData(ctx, uid)
}

// ResetRepo technically identical to TakeDownRepo, for now
func (rm *Manager) ResetRepo(ctx context.Context, uid atp.Aid) error {
	unlock := rm.lockUser(ctx, uid)
	defer unlock()

	return rm.cs.WipeUserData(ctx, uid)
}

// VerifyRepo checks that all records in the repository are readable
func (rm *Manager) VerifyRepo(ctx context.Context, uid atp.Aid) error {
	ses, err := rm.cs.ReadOnlySession(uid)
	if err != nil {
		return err
	}

	r, err := OpenRepo(ctx, ses, ses.BaseCid())
	if err != nil {
		return err
	}

	if err := r.ForEach(ctx, "", func(k string, v cid.Cid) error {
		_, err := ses.Get(ctx, v)
		if err != nil {
			return fmt.Errorf("failed to get record %s (%s): %w", k, v, err)
		}

		return nil
	}); err != nil {
		return err
	}

	return nil
}
