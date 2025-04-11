package pds

import (
	"context"
	"database/sql"
	"fmt"
	"log/slog"
	"strings"
	"time"

	sq "github.com/Masterminds/squirrel"
	"github.com/bluesky-social/indigo/api/atproto"
	"github.com/bluesky-social/indigo/util"
	"github.com/whyrusleeping/go-did"

	"github.com/referendumApp/referendumServices/internal/car"
	"github.com/referendumApp/referendumServices/internal/config"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/events"
	"github.com/referendumApp/referendumServices/internal/indexer"
	"github.com/referendumApp/referendumServices/internal/plc"
	"github.com/referendumApp/referendumServices/internal/repo"
)

type PDS struct {
	db             *database.DB
	repoman        *repo.Manager
	indexer        *indexer.Indexer
	events         *events.EventManager
	log            *slog.Logger
	signingKey     *did.PrivKey
	cs             car.Store
	plc            plc.Client
	handleSuffix   string
	serviceUrl     string
	enforcePeering bool
}

func NewPDS(
	db *database.DB,
	repoman *repo.Manager,
	idxr *indexer.Indexer,
	evts *events.EventManager,
	srvkey *did.PrivKey,
	cfg config.Config,
	cs car.Store,
	plc plc.Client,
) *PDS {
	log := slog.Default().With("system", "pds")

	repoman.SetEventHandler(func(ctx context.Context, evt *repo.Event) {
		if err := idxr.HandleRepoEvent(ctx, evt); err != nil {
			log.Error("handle repo event failed", "user", evt.User, "err", err)
		}
	}, true)

	return &PDS{
		db:             db,
		cs:             cs,
		indexer:        idxr,
		plc:            plc,
		events:         evts,
		repoman:        repoman,
		signingKey:     srvkey,
		handleSuffix:   cfg.HandleSuffix,
		serviceUrl:     cfg.ServiceUrl,
		enforcePeering: false,
		log:            log,
	}
}

// func (s *PDS) handleFedEvent(ctx context.Context, host *Peering, env *events.XRPCStreamEvent) error {
// 	fmt.Printf("[%s] got fed event from %q\n", s.serviceUrl, host.Host)
// 	switch {
// 	case env.RepoCommit != nil:
// 		evt := env.RepoCommit
// 		u, err := s.db.LookupUser(ctx, evt.Repo)
// 		if err != nil {
// 			if !errors.Is(err, pgx.ErrNoRows) {
// 				return fmt.Errorf("looking up event user: %w", err)
// 			}
//
// 			subj, err := s.createExternalUser(ctx, evt.Repo)
// 			if err != nil {
// 				return err
// 			}
//
// 			u = new(User)
// 			u.ID = subj.Uid
// 		}
//
// 		return s.repoman.HandleExternalUserEvent(ctx, host.ID, u.ID, u.Did, evt.Since, evt.Rev, evt.Blocks, evt.Ops)
// 	default:
// 		return fmt.Errorf("invalid fed event")
// 	}
// }
//
// func (s *PDS) createExternalUser(ctx context.Context, did string) (*atp.Person, error) {
// 	doc, err := s.plc.GetDocument(ctx, did)
// 	if err != nil {
// 		return nil, fmt.Errorf("could not locate DID document for followed user: %s", err)
// 	}
//
// 	if len(doc.Service) == 0 {
// 		return nil, fmt.Errorf("external followed user %s had no services in did document", did)
// 	}
//
// 	svc := doc.Service[0]
// 	durl, err := url.Parse(svc.ServiceEndpoint)
// 	if err != nil {
// 		return nil, err
// 	}
//
// 	// TODO: the PDS's DID should also be in the service, we could use that to look up?
// 	var peering Peering
// 	if err := s.db.Find(&peering, "host = ?", durl.Host).Error; err != nil {
// 		return nil, err
// 	}
//
// 	c := &xrpc.Client{Host: svc.ServiceEndpoint}
//
// 	if peering.ID == 0 {
// 		cfg, err := atproto.ServerDescribePDS(ctx, c)
// 		if err != nil {
// 			// TODO: failing this should not halt our indexing
// 			return nil, fmt.Errorf("failed to check unrecognized pds: %w", err)
// 		}
//
// 		// since handles can be anything, checking against this list does not matter...
// 		_ = cfg
//
// 		// TODO: could check other things, a valid response is good enough for now
// 		peering.Host = svc.ServiceEndpoint
//
// 		if err := s.db.Create(&peering).Error; err != nil {
// 			return nil, err
// 		}
// 	}
//
// 	var handle string
// 	if len(doc.AlsoKnownAs) > 0 {
// 		hurl, err := url.Parse(doc.AlsoKnownAs[0])
// 		if err != nil {
// 			return nil, err
// 		}
//
// 		handle = hurl.Host
// 	}
//
// 	// TODO: request this users info from their server to fill out our data...
// 	u := User{
// 		Handle: handle,
// 		Did:    did,
// 		PDS:    peering.ID,
// 	}
//
// 	if err := s.db.Create(&u).Error; err != nil {
// 		return nil, fmt.Errorf("failed to create other pds user: %w", err)
// 	}
//
// 	// okay cool, its a user on a server we are peered with
// 	// lets make a local record of that user for the future
// 	subj := &atp.Person{
// 		Uid:         u.ID,
// 		Handle:      sql.NullString{String: handle, Valid: true},
// 		DisplayName: "missing display name",
// 		Did:         did,
// 		Type:        "",
// 		PDS:         peering.ID,
// 	}
// 	if err := s.db.Create(subj).Error; err != nil {
// 		return nil, err
// 	}
//
// 	return subj, nil
// }

// func (s *PDS) repoEventToFedEvent(ctx context.Context, evt *repo.RepoEvent) (*atproto.SyncSubscribeRepos_Commit, error) {
// 	did, err := s.db.DidForActor(ctx, evt.User)
// 	if err != nil {
// 		return nil, err
// 	}
//
// 	out := &atproto.SyncSubscribeRepos_Commit{
// 		Blocks: evt.RepoSlice,
// 		Repo:   did,
// 		Time:   time.Now().Format(util.ISO8601),
// 		//PrivUid: evt.User,
// 	}
//
// 	for _, op := range evt.Ops {
// 		out.Ops = append(out.Ops, &atproto.SyncSubscribeRepos_RepoOp{
// 			Path:   op.Collection + "/" + op.Rkey,
// 			Action: string(op.Kind),
// 			Cid:    (*lexutil.LexLink)(op.RecCid),
// 		})
// 	}
//
// 	return out, nil
// }
//
// func (s *PDS) readRecordFunc(ctx context.Context, user atp.Uid, c cid.Cid) (lexutil.CBOR, error) {
// 	bs, err := s.cs.ReadOnlySession(user)
// 	if err != nil {
// 		return nil, err
// 	}
//
// 	blk, err := bs.Get(ctx, c)
// 	if err != nil {
// 		return nil, err
// 	}
//
// 	return lexutil.CborDecodeValue(blk.RawData())
// }

// func (s *PDS) HandleResolveDid(c echo.Context) error {
// 	ctx := c.Request().Context()
//
// 	handle := c.Request().Host
// 	if hh := c.Request().Header.Get("Host"); hh != "" {
// 		handle = hh
// 	}
//
// 	u, err := s.db.LookupUserByHandle(ctx, handle)
// 	if err != nil {
// 		return fmt.Errorf("resolving %q: %w", handle, err)
// 	}
//
// 	return c.String(200, u.Did)
// }

func (p *PDS) lookupPeering(ctx context.Context, did string) (*atp.Peering, error) {
	var entity atp.Peering

	if p.enforcePeering && did != "" {
		filter := sq.Eq{"did": did}
		peering, err := database.GetAll(ctx, p.db, entity, filter)
		if err != nil {
			p.log.Error("Failed to lookup peering", "did", did)
			return nil, err
		}

		return peering, nil
	}

	return &entity, nil
}

func (p *PDS) validateHandle(ctx context.Context, handle string) *refErr.APIError {
	if !strings.HasSuffix(handle, p.handleSuffix) {
		fieldErr := refErr.FieldError{Field: "handle", Message: "Invalid handle format"}
		return fieldErr.Invalid()
	}

	if strings.Contains(strings.TrimSuffix(handle, p.handleSuffix), ".") {
		fieldErr := refErr.FieldError{Field: "handle", Message: "Invalid character '.'"}
		return fieldErr.Invalid()
	}

	if exists, err := p.db.UserExists(ctx, "handle", handle); err != nil {
		p.log.ErrorContext(ctx, "Error checking database for user handle", "error", err)
		return refErr.InternalServer()
	} else if exists {
		fieldErr := refErr.FieldError{Field: "handle", Message: "Handle already exists"}
		return fieldErr.Conflict()
	}

	return nil
}

func (p *PDS) UpdateUserHandle(ctx context.Context, u *atp.User, handle string) error {
	if u.Handle.String == handle {
		// no change? move on
		p.log.Warn("attempted to change handle to current handle", "did", u.Did, "handle", handle)
		return nil
	}

	if _, err := p.db.LookupUserByHandle(ctx, handle); err == nil {
		return fmt.Errorf("handle %q is already in use", handle)
	}

	if err := p.plc.UpdateUserHandle(ctx, u.Did, handle); err != nil {
		return fmt.Errorf("failed to update users handle on plc: %w", err)
	}

	if err := p.db.Update(ctx, atp.Person{Uid: u.ID}, "user_id"); err != nil {
		return fmt.Errorf("failed to update handle: %w", err)
	}

	if err := p.db.Update(ctx, atp.User{Handle: sql.NullString{String: handle, Valid: true}}, "user_id"); err != nil {
		return fmt.Errorf("failed to update handle: %w", err)
	}

	if err := p.events.AddEvent(ctx, &events.XRPCStreamEvent{
		RepoHandle: &atproto.SyncSubscribeRepos_Handle{
			Did:    u.Did,
			Handle: handle,
			Time:   time.Now().Format(util.ISO8601),
		},
	}); err != nil {
		return fmt.Errorf("failed to push event: %s", err)
	}

	// Also push an Identity event
	if err := p.events.AddEvent(ctx, &events.XRPCStreamEvent{
		RepoIdentity: &atproto.SyncSubscribeRepos_Identity{
			Did:  u.Did,
			Time: time.Now().Format(util.ISO8601),
		},
	}); err != nil {
		return fmt.Errorf("failed to push event: %s", err)
	}

	return nil
}

func (p *PDS) TakedownRepo(ctx context.Context, did string) error {
	// Push an Account event
	if err := p.events.AddEvent(ctx, &events.XRPCStreamEvent{
		RepoAccount: &atproto.SyncSubscribeRepos_Account{
			Did:    did,
			Active: false,
			Status: &events.AccountStatusTakendown,
			Time:   time.Now().Format(util.ISO8601),
		},
	}); err != nil {
		return fmt.Errorf("failed to push event: %s", err)
	}

	return nil
}

func (p *PDS) SuspendRepo(ctx context.Context, did string) error {
	// Push an Account event
	if err := p.events.AddEvent(ctx, &events.XRPCStreamEvent{
		RepoAccount: &atproto.SyncSubscribeRepos_Account{
			Did:    did,
			Active: false,
			Status: &events.AccountStatusSuspended,
			Time:   time.Now().Format(util.ISO8601),
		},
	}); err != nil {
		return fmt.Errorf("failed to push event: %s", err)
	}

	return nil
}

func (p *PDS) DeactivateRepo(ctx context.Context, did string) error {
	// Push an Account event
	if err := p.events.AddEvent(ctx, &events.XRPCStreamEvent{
		RepoAccount: &atproto.SyncSubscribeRepos_Account{
			Did:    did,
			Active: false,
			Status: &events.AccountStatusDeactivated,
			Time:   time.Now().Format(util.ISO8601),
		},
	}); err != nil {
		return fmt.Errorf("failed to push event: %s", err)
	}

	return nil
}

func (p *PDS) ReactivateRepo(ctx context.Context, did string) error {
	// Push an Account event
	if err := p.events.AddEvent(ctx, &events.XRPCStreamEvent{
		RepoAccount: &atproto.SyncSubscribeRepos_Account{
			Did:    did,
			Active: true,
			Status: &events.AccountStatusActive,
			Time:   time.Now().Format(util.ISO8601),
		},
	}); err != nil {
		return fmt.Errorf("failed to push event: %s", err)
	}

	return nil
}
