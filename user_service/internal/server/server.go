package server

import (
	"context"
	"fmt"
	"log"
	"log/slog"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/referendumApp/referendumServices/internal/app"
	"github.com/referendumApp/referendumServices/internal/aws"
	"github.com/referendumApp/referendumServices/internal/car"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/env-config"
	"github.com/referendumApp/referendumServices/internal/pds"
)

// Server abstraction layer around PDS and App View modules
type Server struct {
	httpServer *http.Server
	db         *database.DB
	mux        *chi.Mux
	av         *app.View
	pds        *pds.PDS
	port       int16
	log        *slog.Logger
}

// New initialize 'Server' struct, setup HTTP routes, and middleware
func New(ctx context.Context, cfg *env.Config, db *database.DB, logger *slog.Logger) (*Server, error) {
	clients, err := aws.NewClients(ctx, cfg.Environment)
	if err != nil {
		return nil, err
	}

	cs, err := car.NewCarStore(ctx, cfg, db, clients.S3, logger)
	if err != nil {
		return nil, err
	}

	// evts := events.NewEventManager(events.NewMemPersister(), logger)

	// kmgr := indexer.NewKeyManager(plc, srvkey, logger)

	// repoman := repo.NewRepoManager(cs, kmgr, logger)

	// rf := indexer.NewRepoFetcher(db, repoman, 10, logger)

	// idxr, err := indexer.NewIndexer(db, evts, plc, rf, false, true, true)
	// if err != nil {
	// 	return nil, err
	// }

	// repoman.SetEventHandler(func(ctx context.Context, evt *repo.Event) {
	// 	if err := idxr.HandleRepoEvent(ctx, evt); err != nil {
	// 		log.ErrorContext(ctx, "Handle repo event failed", "user", evt.User, "err", err)
	// 	}
	// }, true)

	av := app.NewAppView(db, cfg, logger)

	pds, err := pds.NewPDS(ctx, cfg, clients, cs, logger)
	if err != nil {
		return nil, err
	}

	srv := &Server{
		mux:  chi.NewRouter(),
		av:   av,
		pds:  pds,
		port: 80,
		log:  logger,
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

// Start configure HTTP Server, listen and server requests, handle shutdowns gracefully
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

// Shutdown http server and DB
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
