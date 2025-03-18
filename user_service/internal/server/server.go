package server

import (
	"context"
	"fmt"
	"log/slog"
	"net/http"
	"slices"
	"time"

	"github.com/bluesky-social/indigo/api/atproto"
	"github.com/bluesky-social/indigo/carstore"
	"github.com/bluesky-social/indigo/events"
	lexutil "github.com/bluesky-social/indigo/lex/util"
	"github.com/bluesky-social/indigo/plc"
	"github.com/bluesky-social/indigo/repomgr"
	bsutil "github.com/bluesky-social/indigo/util"

	// "github.com/bluesky-social/indigo/xrpc"
	"github.com/go-chi/chi/v5"
	"github.com/golang-jwt/jwt/v5"
	"github.com/gorilla/websocket"
	"github.com/whyrusleeping/go-did"

	"github.com/referendumApp/referendumServices/internal/config"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	"github.com/referendumApp/referendumServices/internal/domain/common"
	"github.com/referendumApp/referendumServices/internal/indexer"
	repo "github.com/referendumApp/referendumServices/internal/repository"
)

type Server struct {
	httpServer *http.Server
	db         *database.Database
	mux        *chi.Mux
	repoman    *repomgr.RepoManager
	indexer    *indexer.Indexer
	events     *events.EventManager
	signingKey *did.PrivKey
	log        *slog.Logger
	jwtConfig  *JWTConfig

	cs  carstore.CarStore
	plc plc.PLCClient

	handleSuffix string
	serviceUrl   string

	port           int16
	enforcePeering bool
}

// Initialize Server and setup HTTP routes and middleware
func New(
	log *slog.Logger,
	db *database.Database,
	serkey *did.PrivKey,
	cfg config.Config,
	cs carstore.CarStore,
	plc plc.PLCClient,
) (*Server, error) {
	evtman := events.NewEventManager(events.NewMemPersister())

	kmgr := indexer.NewKeyManager(plc, serkey)

	repoman := repomgr.NewRepoManager(cs, kmgr)

	rf := indexer.NewRepoFetcher(db, repoman, 10)

	ix, err := indexer.NewIndexer(db, evtman, plc, rf, false, true, true)
	if err != nil {
		return nil, err
	}

	jwtConfig := &JWTConfig{
		SigningKey:    cfg.SecretKey,
		SigningMethod: jwt.SigningMethodHS256,
		Issuer:        cfg.ServiceUrl,
		ContextKey:    "user",
		TokenLookup:   DefaultHeaderAuthorization,
		AuthScheme:    DefaultAuthScheme,
		TokenExpiry:   30 * time.Minute,
		RefreshExpiry: 24 * time.Hour,
	}

	srv := &Server{
		db:             db,
		mux:            chi.NewRouter(),
		port:           80,
		signingKey:     serkey,
		cs:             cs,
		indexer:        ix,
		plc:            plc,
		events:         evtman,
		repoman:        repoman,
		handleSuffix:   cfg.HandleSuffix,
		serviceUrl:     cfg.ServiceUrl,
		jwtConfig:      jwtConfig,
		enforcePeering: false,

		log: log,
	}

	repoman.SetEventHandler(func(ctx context.Context, evt *repomgr.RepoEvent) {
		if err := ix.HandleRepoEvent(ctx, evt); err != nil {
			srv.log.Error("handle repo event failed", "user", evt.User, "err", err)
		}
	}, true)

	// ix.SendRemoteFollow = srv.sendRemoteFollow
	// ix.CreateExternalUser = srv.createExternalUser

	srv.mux.Use(srv.logRequest)
	srv.setupRoutes()

	srv.httpServer = &http.Server{
		Addr:         fmt.Sprintf(":%d", srv.port),
		Handler:      srv.mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  15 * time.Second,
	}

	return srv, nil
}

// Initialize and configure HTTP Server, listen and server requests, handle shutdowns gracefully
func (s *Server) Start(ctx context.Context) error {
	errChan := make(chan error, 1)

	// ListenAndServe is blocking so call it in a go routine to run it concurrently
	go func() {
		fmt.Printf("Server starting on port %d\n", s.port)
		if err := s.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			s.log.Error("Error listening and serving: %s", "error", err)
			errChan <- err
		}
	}()

	select {
	case <-ctx.Done():
		s.log.Info("Shutdown signal received")
	case err := <-errChan:
		return fmt.Errorf("server error: %w", err)
	}

	return nil
}

func (s *Server) Shutdown(ctx context.Context) error {
	s.log.Info("Shutdown server...")
	if err := s.httpServer.Shutdown(ctx); err != nil {
		return fmt.Errorf("shutdown error: %w", err)
	}

	if s.db != nil {
		s.db.Close()
	}

	return nil
}

// func (s *Server) handleFedEvent(ctx context.Context, host *Peering, env *events.XRPCStreamEvent) error {
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
// func (s *Server) createExternalUser(ctx context.Context, did string) (*models.Citizen, error) {
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
// 		cfg, err := atproto.ServerDescribeServer(ctx, c)
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
// 	subj := &models.Citizen{
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

// func (s *Server) repoEventToFedEvent(ctx context.Context, evt *repomgr.RepoEvent) (*atproto.SyncSubscribeRepos_Commit, error) {
// 	did, err := s.db.DidForActor(ctx, evt.User)
// 	if err != nil {
// 		return nil, err
// 	}
//
// 	out := &atproto.SyncSubscribeRepos_Commit{
// 		Blocks: evt.RepoSlice,
// 		Repo:   did,
// 		Time:   time.Now().Format(bsutil.ISO8601),
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
// func (s *Server) readRecordFunc(ctx context.Context, user models.Uid, c cid.Cid) (lexutil.CBOR, error) {
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

// func (s *Server) RunAPIWithListener(listen net.Listener) error {
// 	e := echo.New()
// 	s.echo = e
// 	e.HideBanner = true
// 	e.Use(middleware.LoggerWithConfig(middleware.LoggerConfig{
// 		Format: "method=${method}, uri=${uri}, status=${status} latency=${latency_human}\n",
// 	}))
//
// 	cfg := middleware.JWTConfig{
// 		Skipper: func(c echo.Context) bool {
// 			switch c.Path() {
// 			case "/xrpc/_health":
// 				return true
// 			case "/xrpc/com.atproto.sync.subscribeRepos":
// 				return true
// 			case "/xrpc/com.atproto.account.create":
// 				return true
// 			case "/xrpc/com.atproto.identity.resolveHandle":
// 				return true
// 			case "/xrpc/com.atproto.server.createAccount":
// 				return true
// 			case "/xrpc/com.atproto.server.createSession":
// 				return true
// 			case "/xrpc/com.atproto.server.describeServer":
// 				return true
// 			case "/xrpc/com.atproto.sync.getRepo":
// 				fmt.Println("TODO: currently not requiring auth on get repo endpoint")
// 				return true
// 			case "/xrpc/com.atproto.peering.follow", "/events":
// 				auth := c.Request().Header.Get("Authorization")
//
// 				did := c.Request().Header.Get("DID")
// 				ctx := c.Request().Context()
// 				ctx = context.WithValue(ctx, "did", did)
// 				ctx = context.WithValue(ctx, "auth", auth)
// 				c.SetRequest(c.Request().WithContext(ctx))
// 				return true
// 			case "/.well-known/atproto-did":
// 				return true
// 			case "/takedownRepo":
// 				return true
// 			case "/suspendRepo":
// 				return true
// 			case "/deactivateRepo":
// 				return true
// 			case "/reactivateRepo":
// 				return true
// 			default:
// 				return false
// 			}
// 		},
// 		SigningKey: s.jwtSigningKey,
// 	}
//
// 	e.HTTPErrorHandler = func(err error, ctx echo.Context) {
// 		fmt.Printf("PDS HANDLER ERROR: (%s) %s\n", ctx.Path(), err)
//
// 		// TODO: need to properly figure out where http error codes for error
// 		// types get decided. This spot is reasonable, but maybe a bit weird.
// 		// reviewers, please advise
// 		if errors.Is(err, ErrNoSuchUser) {
// 			ctx.Response().WriteHeader(404)
// 			return
// 		}
//
// 		ctx.Response().WriteHeader(500)
// 	}
//
// 	e.GET("/takedownRepo", func(c echo.Context) error {
// 		ctx := c.Request().Context()
// 		did := c.QueryParam("did")
// 		if did == "" {
// 			return fmt.Errorf("missing did")
// 		}
//
// 		if err := s.TakedownRepo(ctx, did); err != nil {
// 			return err
// 		}
//
// 		return c.String(200, "ok")
// 	})
//
// 	e.GET("/suspendRepo", func(c echo.Context) error {
// 		ctx := c.Request().Context()
// 		did := c.QueryParam("did")
// 		if did == "" {
// 			return fmt.Errorf("missing did")
// 		}
//
// 		if err := s.SuspendRepo(ctx, did); err != nil {
// 			return err
// 		}
//
// 		return c.String(200, "ok")
// 	})
//
// 	e.GET("/deactivateRepo", func(c echo.Context) error {
// 		ctx := c.Request().Context()
// 		did := c.QueryParam("did")
// 		if did == "" {
// 			return fmt.Errorf("missing did")
// 		}
//
// 		if err := s.DeactivateRepo(ctx, did); err != nil {
// 			return err
// 		}
//
// 		return c.String(200, "ok")
// 	})
//
// 	e.GET("/reactivateRepo", func(c echo.Context) error {
// 		ctx := c.Request().Context()
// 		did := c.QueryParam("did")
// 		if did == "" {
// 			return fmt.Errorf("missing did")
// 		}
//
// 		if err := s.ReactivateRepo(ctx, did); err != nil {
// 			return err
// 		}
//
// 		return c.String(200, "ok")
// 	})
//
// 	e.Use(middleware.JWTWithConfig(cfg), s.userCheckMiddleware)
// 	s.RegisterHandlersComAtproto(e)
//
// 	e.GET("/xrpc/com.atproto.sync.subscribeRepos", s.EventsHandler)
// 	e.GET("/xrpc/_health", s.HandleHealthCheck)
// 	e.GET("/.well-known/atproto-did", s.HandleResolveDid)
//
// 	// In order to support booting on random ports in tests, we need to tell the
// 	// Echo instance it's already got a port, and then use its StartServer
// 	// method to re-use that listener.
// 	e.Listener = listen
// 	srv := &http.Server{}
// 	return e.StartServer(srv)
// }

// func (s *Server) HandleResolveDid(c echo.Context) error {
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

// func (s *Server) lookupUser(ctx context.Context, didorhandle string) (*common.User, error) {
// 	if strings.HasPrefix(didorhandle, "did:") {
// 		return s.db.LookupUserByDid(ctx, didorhandle)
// 	}
//
// 	return s.db.LookupUserByHandle(ctx, didorhandle)
// }
//
// func (s *Server) getUser(ctx context.Context) (*common.User, error) {
// 	u, ok := ctx.Value("user").(*common.User)
// 	if !ok {
// 		return nil, fmt.Errorf("auth required")
// 	}
//
// 	//u.Did = ctx.Value("did").(string)
//
// 	return u, nil
// }

// func validateEmail(email string) error {
// 	_, err := mail.ParseAddress(email)
// 	if err != nil {
// 		return err
// 	}
//
// 	return nil
// }
//
// func (s *Server) validateHandle(handle string) error {
// 	if !strings.HasSuffix(handle, s.handleSuffix) {
// 		return fmt.Errorf("invalid handle")
// 	}
//
// 	if strings.Contains(strings.TrimSuffix(handle, s.handleSuffix), ".") {
// 		return fmt.Errorf("invalid handle")
// 	}
//
// 	return nil
// }

func (s *Server) lookupPeering(ctx context.Context, did string) (*atp.Peering, error) {
	var entity atp.Peering

	if s.enforcePeering && did != "" {
		filter := repo.Filter{Column: "did", Op: repo.Eq, Value: did}
		peering, err := database.GetAll(ctx, s.db, entity, filter)
		if err != nil {
			s.log.Error("Failed to lookup peering", "Did", did)
			return nil, err
		}

		return peering, nil
	}

	return &entity, nil
}

func (s *Server) EventsHandler(w http.ResponseWriter, r *http.Request) error {
	ctx := r.Context()

	upgrader := websocket.Upgrader{
		ReadBufferSize:  1 << 10,
		WriteBufferSize: 1 << 10,
		// Allow all origins (be cautious in production)
		CheckOrigin: func(r *http.Request) bool {
			return true
		},
	}

	// Upgrade the connection
	conn, err := upgrader.Upgrade(w, r, r.Header)
	if err != nil {
		http.Error(w, "Could not upgrade connection", http.StatusBadRequest)
		return err
	}

	did := r.Header.Get("DID")
	peering, err := s.lookupPeering(ctx, did)
	if err != nil {
		return err
	}

	ident := getClientIdentifier(r)

	evts, cancel, err := s.events.Subscribe(ctx, ident, func(evt *events.XRPCStreamEvent) bool {
		if !s.enforcePeering {
			return true
		}
		if peering.ID == 0 {
			return true
		}

		return slices.Contains(evt.PrivRelevantPds, peering.ID)
		// for _, pid := range evt.PrivRelevantPds {
		// 	if pid == peering.ID {
		// 		return true
		// 	}
		// }
		//
		// return false
	}, nil)
	if err != nil {
		return err
	}
	defer cancel()

	header := events.EventHeader{Op: events.EvtKindMessage}
	for evt := range evts {
		wc, err := conn.NextWriter(websocket.BinaryMessage)
		if err != nil {
			return err
		}

		var obj lexutil.CBOR

		switch {
		case evt.Error != nil:
			header.Op = events.EvtKindErrorFrame
			obj = evt.Error
		case evt.RepoCommit != nil:
			header.MsgType = "#commit"
			obj = evt.RepoCommit
		case evt.RepoHandle != nil:
			header.MsgType = "#handle"
			obj = evt.RepoHandle
		case evt.RepoIdentity != nil:
			header.MsgType = "#identity"
			obj = evt.RepoIdentity
		case evt.RepoAccount != nil:
			header.MsgType = "#account"
			obj = evt.RepoAccount
		case evt.RepoInfo != nil:
			header.MsgType = "#info"
			obj = evt.RepoInfo
		case evt.RepoMigrate != nil:
			header.MsgType = "#migrate"
			obj = evt.RepoMigrate
		case evt.RepoTombstone != nil:
			header.MsgType = "#tombstone"
			obj = evt.RepoTombstone
		default:
			return fmt.Errorf("unrecognized event kind")
		}

		if err := header.MarshalCBOR(wc); err != nil {
			return fmt.Errorf("failed to write header: %w", err)
		}

		if err := obj.MarshalCBOR(wc); err != nil {
			return fmt.Errorf("failed to write event: %w", err)
		}

		if err := wc.Close(); err != nil {
			return fmt.Errorf("failed to flush-close our event write: %w", err)
		}
	}

	return nil
}

func (s *Server) UpdateUserHandle(ctx context.Context, u *common.User, handle string) error {
	if u.Handle == handle {
		// no change? move on
		s.log.Warn("attempted to change handle to current handle", "did", u.Did, "handle", handle)
		return nil
	}

	if _, err := s.db.LookupUserByHandle(ctx, handle); err == nil {
		return fmt.Errorf("handle %q is already in use", handle)
	}

	if err := s.plc.UpdateUserHandle(ctx, u.Did, handle); err != nil {
		return fmt.Errorf("failed to update users handle on plc: %w", err)
	}

	if err := s.db.Update(ctx, atp.Citizen{Uid: u.ID}, "user_id"); err != nil {
		return fmt.Errorf("failed to update handle: %w", err)
	}

	if err := s.db.Update(ctx, common.User{Handle: handle}, "user_id"); err != nil {
		return fmt.Errorf("failed to update handle: %w", err)
	}

	if err := s.events.AddEvent(ctx, &events.XRPCStreamEvent{
		RepoHandle: &atproto.SyncSubscribeRepos_Handle{
			Did:    u.Did,
			Handle: handle,
			Time:   time.Now().Format(bsutil.ISO8601),
		},
	}); err != nil {
		return fmt.Errorf("failed to push event: %s", err)
	}

	// Also push an Identity event
	if err := s.events.AddEvent(ctx, &events.XRPCStreamEvent{
		RepoIdentity: &atproto.SyncSubscribeRepos_Identity{
			Did:  u.Did,
			Time: time.Now().Format(bsutil.ISO8601),
		},
	}); err != nil {
		return fmt.Errorf("failed to push event: %s", err)
	}

	return nil
}

func (s *Server) TakedownRepo(ctx context.Context, did string) error {
	// Push an Account event
	if err := s.events.AddEvent(ctx, &events.XRPCStreamEvent{
		RepoAccount: &atproto.SyncSubscribeRepos_Account{
			Did:    did,
			Active: false,
			Status: &events.AccountStatusTakendown,
			Time:   time.Now().Format(bsutil.ISO8601),
		},
	}); err != nil {
		return fmt.Errorf("failed to push event: %s", err)
	}

	return nil
}

func (s *Server) SuspendRepo(ctx context.Context, did string) error {
	// Push an Account event
	if err := s.events.AddEvent(ctx, &events.XRPCStreamEvent{
		RepoAccount: &atproto.SyncSubscribeRepos_Account{
			Did:    did,
			Active: false,
			Status: &events.AccountStatusSuspended,
			Time:   time.Now().Format(bsutil.ISO8601),
		},
	}); err != nil {
		return fmt.Errorf("failed to push event: %s", err)
	}

	return nil
}

func (s *Server) DeactivateRepo(ctx context.Context, did string) error {
	// Push an Account event
	if err := s.events.AddEvent(ctx, &events.XRPCStreamEvent{
		RepoAccount: &atproto.SyncSubscribeRepos_Account{
			Did:    did,
			Active: false,
			Status: &events.AccountStatusDeactivated,
			Time:   time.Now().Format(bsutil.ISO8601),
		},
	}); err != nil {
		return fmt.Errorf("failed to push event: %s", err)
	}

	return nil
}

func (s *Server) ReactivateRepo(ctx context.Context, did string) error {
	// Push an Account event
	if err := s.events.AddEvent(ctx, &events.XRPCStreamEvent{
		RepoAccount: &atproto.SyncSubscribeRepos_Account{
			Did:    did,
			Active: true,
			Status: &events.AccountStatusActive,
			Time:   time.Now().Format(bsutil.ISO8601),
		},
	}); err != nil {
		return fmt.Errorf("failed to push event: %s", err)
	}

	return nil
}

func (s *Server) Repoman() *repomgr.RepoManager {
	return s.repoman
}
