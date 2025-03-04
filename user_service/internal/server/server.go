package server

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/referendumApp/referendumServices/internal/config"
	"github.com/referendumApp/referendumServices/internal/database"
)

type Server struct {
	httpServer *http.Server
	db         *database.Database
	mux        *chi.Mux
	secretKey  []byte
	port       int
}

// Initialize Server and setup HTTP routes and middleware
func New(cfg config.Config, db *database.Database) *Server {
	srv := &Server{
		mux:       chi.NewRouter(),
		port:      80,
		secretKey: cfg.SecretKey,
		db:        db,
	}

	srv.mux.Use(logRequest)
	srv.setupRoutes()

	srv.httpServer = &http.Server{
		Addr:         fmt.Sprintf(":%d", srv.port),
		Handler:      srv.mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  15 * time.Second,
	}

	return srv
}

// Initialize and configure HTTP Server, listen and server requests, handle shutdowns gracefully
func (s *Server) Start(ctx context.Context, stderr io.Writer) error {
	errChan := make(chan error, 1)

	// ListenAndServe is blocking so call it in a go routine to run it concurrently
	go func() {
		fmt.Printf("Server starting on port %d\n", s.port)
		if err := s.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Fprintf(stderr, "Error listening and serving: %s", err)
			errChan <- err
		}
	}()

	select {
	case <-ctx.Done():
		fmt.Fprintf(stderr, "Shutdown signal received")
	case err := <-errChan:
		return fmt.Errorf("server error: %w", err)
	}

	return nil
}

func (s *Server) Shutdown(ctx context.Context) error {
	fmt.Println("Shutting down server...")
	if err := s.httpServer.Shutdown(ctx); err != nil {
		return fmt.Errorf("shutdown error: %w", err)
	}

	if s.db != nil {
		if err := s.db.Close(); err != nil {
			return fmt.Errorf("database close error: %w", err)
		}
	}

	return nil
}
