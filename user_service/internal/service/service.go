package service

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"log/slog"
	"net/http"
	"strconv"
	"time"

	"github.com/aws/aws-sdk-go-v2/service/secretsmanager"
	"github.com/go-chi/chi/v5"
	"github.com/referendumApp/referendumServices/internal/app"
	"github.com/referendumApp/referendumServices/internal/aws"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	env "github.com/referendumApp/referendumServices/internal/env-config"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/pds"
)

// SystemAPIKeySecret represents the structure of the system API key secret
type SystemAPIKeySecret struct {
	APIKey string `json:"apiKey"`
	DID    string `json:"did,omitempty"`
	AID    string `json:"aid,omitempty"`
}

// IsUserCreated returns true if the system user has been created (DID and AID are present)
func (s *SystemAPIKeySecret) IsUserCreated() bool {
	return s.DID != "" && s.AID != ""
}

// GetAIDAsAtp converts the AID string to atp.Aid and validates it's valid
func (s *SystemAPIKeySecret) GetAIDAsAtp() (atp.Aid, error) {
	if s.AID == "" {
		return 0, errors.New("AID is empty")
	}

	// Parse as uint64 directly to avoid overflow issues
	aidUint, err := strconv.ParseUint(s.AID, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("failed to parse AID: %w", err)
	}

	return atp.Aid(aidUint), nil
}

// SetUserData sets the DID and AID after user creation
func (s *SystemAPIKeySecret) SetUserData(did string, aid atp.Aid) {
	s.DID = did
	s.AID = strconv.FormatUint(uint64(aid), 10)
}

// TODO - implement SystemAPI secret with did key & rotation

// Service abstraction layer around PDS and App View modules
type Service struct {
	httpServer *http.Server
	mux        *chi.Mux
	av         *app.View
	pds        *pds.PDS
	log        *slog.Logger
	port       int16
	cancelCh   chan struct{}
	clients    *aws.Clients
	config     *env.Config
}

// New initialize 'Service' struct, setup HTTP routes, and middleware
func New(
	ctx context.Context,
	av *app.View,
	pds *pds.PDS,
	clients *aws.Clients,
	config *env.Config,
	logger *slog.Logger,
) (*Service, error) {
	srv := &Service{
		mux:      chi.NewRouter(),
		av:       av,
		pds:      pds,
		clients:  clients,
		config:   config,
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

// AuthenticateSystemUser validates the API key and ensures system user exists
func (s *Service) AuthenticateSystemUser(ctx context.Context, apiKey string) (*atp.Aid, *string, error) {
	secret, err := s.validateApiKeyAndGetSecret(ctx, apiKey)
	if err != nil {
		return nil, nil, err
	}

	if err = s.ensureSystemUserExists(ctx, secret); err != nil {
		return nil, nil, fmt.Errorf("failed to ensure system user exists: %w", err)
	}

	aid, err := secret.GetAIDAsAtp()
	if err != nil {
		return nil, nil, fmt.Errorf("failed to get AID: %w", err)
	}

	return &aid, &secret.DID, nil
}

// validateApiKeyAndGetSecret validates the provided API key against stored secret
func (s *Service) validateApiKeyAndGetSecret(ctx context.Context, apiKey string) (*SystemAPIKeySecret, error) {
	secret, err := s.getSystemApiKeySecret(ctx)
	if err != nil {
		return nil, err
	}

	if apiKey != secret.APIKey {
		return nil, errors.New("invalid API key")
	}

	return secret, nil
}

// ensureSystemUserExists creates system user if it doesn't exist, updates secret if created
func (s *Service) ensureSystemUserExists(ctx context.Context, secret *SystemAPIKeySecret) error {
	if secret.IsUserCreated() {
		return nil // User already exists
	}

	return s.createSystemUser(ctx, secret)
}

func (s *Service) createSystemUser(ctx context.Context, secret *SystemAPIKeySecret) error {
	actor, apiErr := s.pds.CreateActor(
		ctx,
		s.config.SystemUserConfig.Handle,
		s.config.SystemUserConfig.DisplayName,
		s.config.SystemUserConfig.Email,
		&atp.AuthSettings{ApiKey: secret.APIKey},
		nil,
	)
	if apiErr != nil {
		return fmt.Errorf("failed to create actor: %w", apiErr)
	}

	if err := s.av.CreateUser(ctx, actor, s.config.SystemUserConfig.DisplayName); err != nil {
		return fmt.Errorf("failed to create user: %w", err)
	}

	_, err := s.pds.CreateNewUserRepo(ctx, actor, s.config.SystemUserConfig.DisplayName)
	if err != nil {
		return fmt.Errorf("failed to create user repo: %w", err)
	}

	secret.SetUserData(actor.Did, actor.ID)

	return s.updateSystemApiKeySecret(ctx, secret)
}

func (s *Service) getSystemApiKeySecret(ctx context.Context) (*SystemAPIKeySecret, error) {
	secretKeyName := s.config.SystemUserConfig.SecretName
	input := &secretsmanager.GetSecretValueInput{
		SecretId: &secretKeyName,
	}

	result, err := s.clients.SECRETSMANAGER.GetSecretValue(ctx, input)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to get secret", "error", err)
		return nil, errors.New("secret value doesn't exist")
	}

	if result.SecretString == nil {
		return nil, errors.New("secret value is empty")
	}

	var secret SystemAPIKeySecret
	if err := json.Unmarshal([]byte(*result.SecretString), &secret); err != nil {
		return nil, fmt.Errorf("failed to parse secret JSON: %w", err)
	}

	if secret.APIKey == "" {
		return nil, errors.New("API key is missing from secret")
	}

	return &secret, nil
}

func (s *Service) updateSystemApiKeySecret(ctx context.Context, secret *SystemAPIKeySecret) error {
	secretBytes, err := json.Marshal(secret) //nolint:errchkjson // secret struct is guaranteed safe to marshal
	if err != nil {
		return fmt.Errorf("failed to marshal secret to JSON: %w", err)
	}

	secretString := string(secretBytes)
	secretKeyName := s.config.SystemUserConfig.SecretName

	params := &secretsmanager.PutSecretValueInput{
		SecretId:     &secretKeyName,
		SecretString: &secretString,
	}

	_, err = s.clients.SECRETSMANAGER.PutSecretValue(ctx, params)
	if err != nil {
		return fmt.Errorf("failed to update secret in AWS Secrets Manager: %w", err)
	}

	s.log.InfoContext(ctx, "Successfully updated system API key secret")
	return nil
}

// getAuthenticatedSystemIds returns just the IDs for the authenticated system user
func (s *Service) getAuthenticatedSystemIds(ctx context.Context) (*atp.Aid, *string, *refErr.APIError) {
	aid, ok := ctx.Value(systemAidKey{}).(atp.Aid)
	if !ok {
		return nil, nil, refErr.Unauthorized("System user not authenticated")
	}

	did, ok := ctx.Value(systemDidKey{}).(string)
	if !ok {
		return nil, nil, refErr.Unauthorized("System user not authenticated")
	}

	return &aid, &did, nil
}
