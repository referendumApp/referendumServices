package server

import (
	"context"
	"fmt"
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
func New(db *database.DB, srvkey *did.PrivKey, cfg *env.Config, cs car.Store, plc plc.Client) (*Server, error) {
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
