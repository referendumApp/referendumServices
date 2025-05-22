//go:build integration

package service

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"log"
	"log/slog"
	"net/http"
	"net/url"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/referendumApp/referendumServices/internal/app"
	"github.com/referendumApp/referendumServices/internal/aws"
	"github.com/referendumApp/referendumServices/internal/car"
	"github.com/referendumApp/referendumServices/internal/database"
	refApp "github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	"github.com/referendumApp/referendumServices/internal/env-config"
	"github.com/referendumApp/referendumServices/internal/keymgr"
	"github.com/referendumApp/referendumServices/internal/pds"
	"github.com/referendumApp/referendumServices/internal/plc"
	"github.com/referendumApp/referendumServices/internal/util"
	"github.com/referendumApp/referendumServices/testutil"
	"github.com/stretchr/testify/assert"
)

const (
	baseUrl = "http://localhost:80"
	handle  = "k1ng.referendumapp.com"
	email   = "ken@referendumapp.com"
	pw      = "Testing123$"
)

var (
	testService  *Service
	client       *http.Client
	accessToken  string
	refreshToken string
)

func setupAndRunTests(m *testing.M, servChErr chan error) int {
	defer close(servChErr)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	logger := slog.Default()
	cfg, err := env.LoadConfig()
	if err != nil {
		log.Printf("Failed to load environment variables: %v\n", err)
		os.Exit(1)
	}

	docker, err := testutil.SetupDocker()
	if err != nil {
		log.Printf("Failed to setup docker API and network: %v\n", err)
		return 1
	}
	defer docker.CleanupDocker()

	pc, err := docker.SetupPostgres(ctx, cfg.DBConfig)
	if err != nil {
		log.Printf("Failed to setup postgres container: %v\n", err)
		return 1
	}
	defer pc.CleanupPostgres(docker)

	sc, err := docker.SetupS3(ctx)
	if err != nil {
		log.Printf("Failed to setup minio container: %v\n", err)
		return 1
	}
	defer sc.CleanupS3(docker)

	kms, err := docker.SetupKMS(ctx, cfg)
	if err != nil {
		log.Printf("Failed to setup kms container: %v\n", err)
		return 1
	}
	defer kms.CleanupKMS(docker)

	db, err := database.Connect(ctx, cfg.DBConfig, logger)
	if err != nil {
		return 1
	}
	defer db.Close()

	av := app.NewAppView(db, cfg.DBConfig.AtpDBSchema, cfg.HandleSuffix, logger)

	clients, err := aws.NewClients(ctx, cfg.Env)
	if err != nil {
		return 1
	}

	cs, err := car.NewCarStore(ctx, db, clients.S3, cfg.DBConfig.CarDBSchema, cfg.Env, cfg.CarDir, logger)
	if err != nil {
		return 1
	}

	km, err := keymgr.NewKeyManager(
		ctx,
		clients.KMS,
		clients.S3,
		cfg.Env,
		cfg.KeyDir,
		cfg.RecoveryKey,
		util.RefreshExpiry,
		util.AccessExpiry-(5*time.Minute),
		logger,
	)
	if err != nil {
		return 1
	}

	plc := plc.NewTestClient(km)

	pds, err := pds.NewPDS(ctx, km, plc, cs, cfg.HandleSuffix, cfg.ServiceUrl, cfg.SecretKey, logger)
	if err != nil {
		return 1
	}

	testService, err = New(ctx, av, pds, logger)
	if err != nil {
		return 1
	}

	go func() {
		servChErr <- testService.Start(ctx)
	}()

	time.Sleep(1 * time.Second)

	client = &http.Client{Timeout: 5 * time.Second}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, baseUrl+"/health", nil)
	if err != nil {
		log.Printf("Failed to create health request: %v\n", err)
		return 1
	}

	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Health request failed: %v\n", err)
		return 1
	}
	defer func() {
		_ = resp.Body.Close()
	}()
	if resp.StatusCode != http.StatusOK {
		log.Printf("Server did not start properly, got status %v\n", resp.Status)
		return 1
	}

	exitCode := m.Run()

	cancel()

	return exitCode
}

func TestMain(m *testing.M) {
	servChErr := make(chan error, 1)

	exitCode := setupAndRunTests(m, servChErr)

	if err := <-servChErr; err != nil && !errors.Is(err, context.Canceled) {
		log.Fatalf("Server exited with error: %v\n", err)
	}
	os.Exit(exitCode)
}

type testRequest struct {
	method  string
	path    string
	body    any
	headers map[string]string
}

func (tr *testRequest) handleJsonRequest(t *testing.T) *http.Request {
	reqBody, err := json.Marshal(tr.body)
	assert.NoError(t, err, "Failed to marshal request body")

	req, err := http.NewRequestWithContext(
		context.Background(),
		tr.method,
		baseUrl+tr.path,
		bytes.NewReader(reqBody),
	)
	assert.NoError(t, err, "Failed to create HTTP request")

	for k, v := range tr.headers {
		req.Header.Set(k, v)
	}

	return req
}

func (tr *testRequest) handleFormRequest(t *testing.T) *http.Request {
	form, ok := tr.body.(url.Values)
	assert.True(t, ok, "Request body must be 'url.Values'")

	req, err := http.NewRequestWithContext(
		context.Background(),
		tr.method,
		baseUrl+tr.path,
		strings.NewReader(form.Encode()),
	)
	assert.NoError(t, err, "Failed to create HTTP request")

	for k, v := range tr.headers {
		req.Header.Set(k, v)
	}

	return req
}

type testResponse struct {
	status int
	body   any
}

func (e *testResponse) getResponse(t *testing.T, req *http.Request) int {
	resp, err := client.Do(req)
	assert.NoError(t, err, "HTTP request failed")
	defer resp.Body.Close()

	// Always log request details for debugging
	t.Logf("Request: %s %s", req.Method, req.URL.String())
	if len(req.Header) > 0 {
		t.Logf("Request Headers: %+v", req.Header)
	}

	// Log actual response details
	t.Logf("Response Status: %d %s", resp.StatusCode, resp.Status)
	if len(resp.Header) > 0 {
		t.Logf("Response Headers: %+v", resp.Header)
	}

	// Read the response body to log and validate it
	bodyBytes, readErr := io.ReadAll(resp.Body)
	if readErr != nil {
		t.Logf("Failed to read response body: %v", readErr)
	} else if len(bodyBytes) > 0 {
		t.Logf("Response Body: %s", string(bodyBytes))
	}

	// Check if status code matches expected
	if e.status != resp.StatusCode {
		t.Errorf("Status code mismatch: expected %d, got %d", e.status, resp.StatusCode)
		t.Errorf("Response details logged above")
	}

	// If we have an expected response body and the request was successful, try to decode
	if e.body != nil && resp.StatusCode < 300 && len(bodyBytes) > 0 {
		// Create a new reader from the bytes we already read
		bodyReader := bytes.NewReader(bodyBytes)

		decodeErr := json.NewDecoder(bodyReader).Decode(e.body)
		if decodeErr != nil {
			t.Errorf("Error decoding response body: %v", decodeErr)
			t.Errorf("Raw response body: %s", string(bodyBytes))
		} else {
			// Validate the decoded structure
			valErr := util.Validate.Struct(e.body)
			if valErr != nil {
				t.Errorf("Error validating response body structure: %v", valErr)
				t.Errorf("Decoded body: %+v", e.body)
			}
		}
	}

	// For error responses, always log what we got vs what we expected
	if resp.StatusCode >= 400 {
		t.Logf("Error response received - Expected status: %d, Got status: %d", e.status, resp.StatusCode)
		if len(bodyBytes) > 0 {
			// Try to parse as JSON error for better formatting
			var errorResp map[string]interface{}
			if json.Unmarshal(bodyBytes, &errorResp) == nil {
				t.Logf("Parsed error response: %+v", errorResp)
			}
		}
	}

	return resp.StatusCode
}

type testCase struct {
	name     string
	request  testRequest
	response testResponse
	expected any
}

func TestCreateAccount(t *testing.T) {
	tests := []testCase{
		{
			"Create Account",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       email,
					Handle:      handle,
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusCreated,
				body:   &refApp.ServerCreateAccount_Output{},
			},
			nil,
		},
		{
			"Create Account",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       "kenny@gmail.com",
					Handle:      "k1-ng.referendumapp.com",
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusCreated,
				body:   &refApp.ServerCreateAccount_Output{},
			},
			nil,
		},
		{
			"Create Account w/ Duplicate Handle",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       "kenny@referendumapp.com",
					Handle:      handle,
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusConflict,
			},
			nil,
		},
		{
			"Create Account w/ Duplicate Email",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       email,
					Handle:      "ken.referendumapp.com",
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusConflict,
			},
			nil,
		},
		{
			"Create Account w/ Invalid Handle",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       email,
					Handle:      "k1ng",
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
			},
			nil,
		},
		{
			"Create Account w/ Invalid Handle",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       email,
					Handle:      "k1_ng.referendumapp.com",
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
			},
			nil,
		},
		{
			"Create Account w/ Invalid Handle",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       email,
					Handle:      "k!ng.referendumapp.com",
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
			},
			nil,
		},
		{
			"Create Account w/ Invalid Handle",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       "kenny@gmail.com",
					Handle:      "-k1ng.referendumapp.com",
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
			},
			nil,
		},
		{
			"Create Account w/ Invalid Handle",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       email,
					Handle:      ".k1ng.referendumapp.com",
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
			},
			nil,
		},
		{
			"Create Account w/ Invalid Email",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       "kengmail.com",
					Handle:      handle,
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
			},
			nil,
		},
		{
			"Create Account w/ Invalid Password",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       email,
					Handle:      handle,
					Password:    "test",
				},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
			},
			nil,
		},
		{
			"Create Account w/ Invalid Display Name",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken.",
					Email:       email,
					Handle:      handle,
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
			},
			nil,
		},
		{
			"Create Account w/ Missing Display Name",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					Email:    email,
					Handle:   handle,
					Password: pw,
				},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
			},
			nil,
		},
		{
			"Create Account w/ Missing Email",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Handle:      handle,
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
			},
			nil,
		},
		{
			"Create Account w/ Missing Handle",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       email,
					Password:    pw,
				},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
			},
			nil,
		},
		{
			"Create Account w/ Missing Password",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/signup",
				body: refApp.ServerCreateAccount_Input{
					DisplayName: "Ken",
					Email:       email,
					Handle:      handle,
				},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
			},
			nil,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			req := tc.request.handleJsonRequest(t)
			tc.response.getResponse(t, req)
		})
	}
}

func stringPtr(s string) *string {
	return &s
}
