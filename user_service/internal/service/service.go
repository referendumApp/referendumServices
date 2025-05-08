package service

import (
	"context"
	"fmt"
	"log"
	"log/slog"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/referendumApp/referendumServices/internal/app"
	"github.com/referendumApp/referendumServices/internal/pds"
)

// Service abstraction layer around PDS and App View modules
type Service struct {
	httpServer *http.Server
	mux        *chi.Mux
	av         *app.View
	pds        *pds.PDS
	log        *slog.Logger
	port       int16
	cancelCh   chan struct{}
}

// New initialize 'Service' struct, setup HTTP routes, and middleware
func New(ctx context.Context, av *app.View, pds *pds.PDS, logger *slog.Logger) (*Service, error) {
	srv := &Service{
		mux:      chi.NewRouter(),
		av:       av,
		pds:      pds,
		log:      logger,
		port:     80,
		cancelCh: make(chan struct{}),
	}

	srv.mux.Use(func(next http.Handler) http.Handler {
		return srv.gracefulShutdown(next, srv.cancelCh)
	})

	srv.mux.Use(srv.logRequest)
	srv.mux.Use(srv.requestTimeout)
	srv.setupRoutes()

	srv.httpServer = &http.Server{
		Addr:         fmt.Sprintf(":%d", srv.port),
		Handler:      srv.mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  15 * time.Second,
	}

	return srv, nil
}

// Start configure HTTP Server, listen and server requests, handle shutdowns gracefully
func (s *Service) Start(ctx context.Context) error {
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
		close(s.cancelCh)
		return s.Shutdown()
	case err := <-errChan:
		return fmt.Errorf("server error: %w", err)
	}
}

// Shutdown http server
func (s *Service) Shutdown() error {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	log.Println("Shutting down HTTP server")
	if err := s.httpServer.Shutdown(ctx); err != nil {
		log.Printf("HTTP server shutdown error: %v\n", err)
		return err
	}

	if err := s.pds.Shutdown(ctx); err != nil {
		return err
	}

	log.Println("Server shutdown complete")
	return nil
}
