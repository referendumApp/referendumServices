package server

import (
	"context"
	"crypto/rand"
	"fmt"
	"log"
	"log/slog"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/whyrusleeping/go-did"

	"github.com/referendumApp/referendumServices/internal/app"
	"github.com/referendumApp/referendumServices/internal/car"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/env"
	"github.com/referendumApp/referendumServices/internal/events"
	"github.com/referendumApp/referendumServices/internal/indexer"
	"github.com/referendumApp/referendumServices/internal/pds"
	"github.com/referendumApp/referendumServices/internal/plc"
	"github.com/referendumApp/referendumServices/internal/repo"
)

type Server struct {
	httpServer *http.Server
	db         *database.DB
	mux        *chi.Mux
	av         *app.View
	pds        *pds.PDS
	port       int16
	log        *slog.Logger
}

// Initialize Server and setup HTTP routes and middleware
func New(ctx context.Context, cfg *env.Config, db *database.DB) (*Server, error) {
	log.Println("Generating private key")
	srvkey, err := did.GeneratePrivKey(rand.Reader, did.KeyTypeSecp256k1)
	if err != nil {
		log.Println("Failed to generate private key")
		return nil, err
	}
	log.Println("Successfully generated private key!")

	plc := plc.NewPLCServer(cfg.PLCHost)

	cs, err := car.NewCarStore(ctx, cfg, db)
	if err != nil {
		return nil, err
	}

	evts := events.NewEventManager(events.NewMemPersister())

	kmgr := indexer.NewKeyManager(plc, srvkey)

	repoman := repo.NewRepoManager(cs, kmgr)

	rf := indexer.NewRepoFetcher(db, repoman, 10)

	idxr, err := indexer.NewIndexer(db, evts, plc, rf, false, true, true)
	if err != nil {
		return nil, err
	}

	av := app.NewAppView(db, repoman, cs, cfg)

	pds := pds.NewPDS(repoman, idxr, evts, srvkey, cfg, cs, plc)

	srv := &Server{
		mux:  chi.NewRouter(),
		av:   av,
		pds:  pds,
		port: 80,
		log:  slog.Default().With("system", "server"),
	}

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
		log.Printf("Server starting on port %d\n", s.port)
		if err := s.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Println("Error listening and serving")
			errChan <- err
		}
	}()

	select {
	case <-ctx.Done():
		log.Println("Shutdown signal received")
	case err := <-errChan:
		return fmt.Errorf("server error: %w", err)
	}

	return nil
}

func (s *Server) Shutdown(ctx context.Context) error {
	log.Println("Shutdown server...")
	if err := s.httpServer.Shutdown(ctx); err != nil {
		return fmt.Errorf("shutdown error: %w", err)
	}

	if s.db != nil {
		s.db.Close()
	}

	return nil
}
