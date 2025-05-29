package service

import (
	"context"
	"errors"
	"fmt"
	"log"
	"log/slog"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/referendumApp/referendumServices/internal/app"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
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

func (s *Service) validateSystemApiKey(ctx context.Context, apiKey string) (*atp.Aid, *string, error) {
	secret := map[string]string{
		"apiKey": "TEST_API_KEY",
	}

	if apiKey != secret["apiKey"] {
		return nil, nil, errors.New("invalid API key")
	}

	var did string
	var aid atp.Aid

	if storedDid, exists := secret["did"]; !exists || storedDid == "" {
		if err := s.createSystemUser(ctx, secret); err != nil {
			return nil, nil, fmt.Errorf("failed to create system user: %w", err)
		}
		did = secret["did"]
		aidInt, _ := strconv.ParseInt(secret["aid"], 10, 64)
		if aidInt < 0 {
			return nil, nil, errors.New("aid cannot be negative")
		}
		aid = atp.Aid(aidInt)
	} else {
		did = storedDid
		aidInt, _ := strconv.ParseInt(secret["aid"], 10, 64)
		if aidInt < 0 {
			return nil, nil, errors.New("aid cannot be negative")
		}
		aid = atp.Aid(aidInt)
	}

	return &aid, &did, nil
}

func (s *Service) createSystemUser(ctx context.Context, secret map[string]string) error {
	handle := "system.referendumapp.com"
	displayName := "System User"
	email := "system@referendumapp.com"

	actor, err := s.pds.CreateActor(ctx, handle, displayName, "", email, "", "system")
	if err != nil {
		return err
	}

	user, err := s.av.CreateUser(ctx, actor, displayName)
	if err != nil {
		return err
	}

	_, err = s.pds.CreateNewUserRepo(ctx, actor, user)
	if err != nil {
		return err
	}

	secret["did"] = actor.Did
	secret["aid"] = strconv.FormatUint(uint64(actor.ID), 10)

	return s.updateSecret(secret)
}

func (s *Service) updateSecret(secret map[string]string) error {
	return nil
}
