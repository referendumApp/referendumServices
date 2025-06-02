//go:build integration

package service

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"log/slog"
	"net/http"
	"net/url"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
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
	baseUrl     = "http://localhost:80"
	handle      = "k1ng.referendumapp.com"
	email       = "ken@referendumapp.com"
	pw          = "Testing123$"
	adminApiKey = "TEST_API_KEY"
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

	sc, err := docker.SetupLocalStack(ctx)
	if err != nil {
		log.Printf("Failed to setup s3 container: %v\n", err)
		return 1
	}
	defer sc.CleanupLocalStack(docker)

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

	testService, err = New(ctx, av, pds, clients, cfg, logger)
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

func TestSession(t *testing.T) {
	createTests := []testCase{
		{
			"Create Session w/ Handle",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/login",
				body: url.Values{
					"grantType": {"password"},
					"username":  {handle},
					"password":  {pw},
				},
				headers: map[string]string{"Content-Type": "application/x-www-form-urlencoded"},
			},
			testResponse{
				status: http.StatusCreated,
				body:   &refApp.ServerCreateSession_Output{},
			},
			nil,
		},
		{
			"Create Session w/ Email",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/login",
				body: url.Values{
					"grantType": {"password"},
					"username":  {email},
					"password":  {pw},
				},
				headers: map[string]string{"Content-Type": "application/x-www-form-urlencoded"},
			},
			testResponse{
				status: http.StatusCreated,
				body:   &refApp.ServerCreateSession_Output{},
			},
			nil,
		},
		{
			"Create Session w/ Invalid Grant",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/login",
				body: url.Values{
					"grantType": {"test"},
					"username":  {email},
					"password":  {pw},
				},
				headers: map[string]string{"Content-Type": "application/x-www-form-urlencoded"},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
				body:   &refApp.ServerCreateSession_Output{},
			},
			nil,
		},
		{
			"Create Session w/ Incorrect Password",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/login",
				body: url.Values{
					"grantType": {"password"},
					"username":  {email},
					"password":  {"SFKJKLj4923049023jfjd!"},
				},
				headers: map[string]string{"Content-Type": "application/x-www-form-urlencoded"},
			},
			testResponse{
				status: http.StatusNotFound,
				body:   &refApp.ServerCreateSession_Output{},
			},
			nil,
		},
		{
			"Create Session w/ Incorrect Username",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/login",
				body: url.Values{
					"grantType": {"password"},
					"username":  {"wrong.referendumapp.com"},
					"password":  {pw},
				},
				headers: map[string]string{"Content-Type": "application/x-www-form-urlencoded"},
			},
			testResponse{
				status: http.StatusNotFound,
				body:   &refApp.ServerCreateSession_Output{},
			},
			nil,
		},
		{
			"Create Session w/ Missing Username",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/login",
				body: url.Values{
					"grantType": {"password"},
					"password":  {pw},
				},
				headers: map[string]string{"Content-Type": "application/x-www-form-urlencoded"},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
				body:   &refApp.ServerCreateSession_Output{},
			},
			nil,
		},
		{
			"Create Session w/ Missing Password",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/login",
				body: url.Values{
					"grantType": {"password"},
					"username":  {handle},
				},
				headers: map[string]string{"Content-Type": "application/x-www-form-urlencoded"},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
				body:   &refApp.ServerCreateSession_Output{},
			},
			nil,
		},
	}

	for _, tc := range createTests {
		t.Run(tc.name, func(t *testing.T) {
			req := tc.request.handleFormRequest(t)
			tc.response.getResponse(t, req)

			session, ok := tc.response.body.(*refApp.ServerCreateSession_Output)
			assert.True(t, ok, "Response body should be *ServerCreateSession_Output")

			if session.AccessToken != "" && session.RefreshToken != "" {
				accessToken = session.AccessToken
				refreshToken = session.RefreshToken
			}
		})
	}

	testRefreshToken, err := jwt.NewWithClaims(
		jwt.SigningMethodHS256,
		jwt.MapClaims{"sub": "1", "did": "did:plc:fjadklfjlkadsjf", "iss": "test", "type": "refresh"},
	).SignedString(bytes.NewBufferString("test").Bytes())
	assert.NoError(t, err, "Error generating test token")

	refreshTests := []testCase{
		{
			"Refresh Session",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/refresh",
				body: refApp.ServerRefreshSession_Input{
					RefreshToken: refreshToken,
				},
			},
			testResponse{
				status: http.StatusOK,
				body:   &refApp.ServerRefreshSession_Output{},
			},
			nil,
		},
		{
			"Refresh Session w/ Missing Token",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/refresh",
				body:   refApp.ServerRefreshSession_Input{},
			},
			testResponse{
				status: http.StatusUnprocessableEntity,
				body:   &refApp.ServerRefreshSession_Output{},
			},
			nil,
		},
		{
			"Refresh Session w/ Invalid Token",
			testRequest{
				method: http.MethodPost,
				path:   "/auth/refresh",
				body: refApp.ServerRefreshSession_Input{
					RefreshToken: testRefreshToken,
				},
			},
			testResponse{
				status: http.StatusUnauthorized,
				body:   &refApp.ServerRefreshSession_Output{},
			},
			nil,
		},
	}

	for _, tc := range refreshTests {
		t.Run(tc.name, func(t *testing.T) {
			req := tc.request.handleJsonRequest(t)
			tc.response.getResponse(t, req)

			session, ok := tc.response.body.(*refApp.ServerRefreshSession_Output)
			assert.True(t, ok, "Response body should be *ServerRefreshSession_Output")

			if session.AccessToken != "" && session.RefreshToken != "" {
				accessToken = session.AccessToken
				refreshToken = session.RefreshToken
				t.Logf("Tokens Refreshed: Access: %s Refresh %s", accessToken, refreshToken)
			}
		})
	}

	testAccessToken, err := jwt.NewWithClaims(
		jwt.SigningMethodHS256,
		jwt.MapClaims{"sub": "1", "did": "did:plc:fjadklfjlkadsjf", "iss": "test", "type": "access"},
	).SignedString(bytes.NewBufferString("test").Bytes())
	assert.NoError(t, err, "Error generating test token")

	deleteSessionTests := []testCase{
		{
			"Delete Session w/ Invalid Token",
			testRequest{
				method:  http.MethodDelete,
				path:    "/auth/session",
				headers: map[string]string{"Authorization": "Bearer " + testAccessToken},
			},
			testResponse{
				status: http.StatusBadRequest,
			},
			nil,
		},
		{
			"Delete Session",
			testRequest{
				method:  http.MethodDelete,
				path:    "/auth/session",
				headers: map[string]string{"Authorization": "Bearer " + accessToken},
			},
			testResponse{
				status: http.StatusOK,
			},
			nil,
		},
	}

	for _, tc := range deleteSessionTests {
		t.Run(tc.name, func(t *testing.T) {
			req := tc.request.handleJsonRequest(t)
			tc.response.getResponse(t, req)
		})
	}

	deleteAcctTests := []testCase{
		{
			"Delete Account w/ Invalid Token",
			testRequest{
				method:  http.MethodDelete,
				path:    "/auth/account",
				headers: map[string]string{"Authorization": "Bearer " + testAccessToken},
			},
			testResponse{
				status: http.StatusBadRequest,
			},
			nil,
		},
		{
			"Delete Account",
			testRequest{
				method:  http.MethodDelete,
				path:    "/auth/account",
				headers: map[string]string{"Authorization": "Bearer " + accessToken},
			},
			testResponse{
				status: http.StatusOK,
			},
			nil,
		},
		{
			"Delete Account Again",
			testRequest{
				method:  http.MethodDelete,
				path:    "/auth/account",
				headers: map[string]string{"Authorization": "Bearer " + accessToken},
			},
			testResponse{
				status: http.StatusBadRequest,
			},
			nil,
		},
	}

	for _, tc := range deleteAcctTests {
		t.Run(tc.name, func(t *testing.T) {
			req := tc.request.handleJsonRequest(t)
			sc := tc.response.getResponse(t, req)

			if sc == http.StatusOK {
				loginReq := testRequest{
					method: http.MethodPost,
					path:   "/auth/login",
					body: url.Values{
						"grantType": {"password"},
						"username":  {handle},
						"password":  {pw},
					},
					headers: map[string]string{"Content-Type": "application/x-www-form-urlencoded"},
				}

				expectedResp := testResponse{
					status: http.StatusNotFound,
					body:   nil,
				}

				checkReq := loginReq.handleFormRequest(t)
				expectedResp.getResponse(t, checkReq)
			}
		})
	}
}

func TestLegislator(t *testing.T) {
	legislatorID := int64(12345)
	duplicateID := int64(12345)
	updateID := int64(54321)
	deleteID := int64(77777)

	createTestLegislator := func(id int64, name string) (*refApp.ServerCreateLegislator_Output, error) {
		createReq := testRequest{
			method: http.MethodPost,
			path:   "/legislators",
			body: refApp.ServerCreateLegislator_Input{
				LegislatorId: id,
				Name:         name,
				District:     fmt.Sprintf("WA-SD-%02d", id%100),
				Party:        "Independent",
				Role:         "Senator",
				State:        "WA",
				Legislature:  "US",
				Address:      stringPtr(fmt.Sprintf("%d Capitol St", id)),
				Phone:        stringPtr(fmt.Sprintf("+1206555%04d", id%10000)),
			},
			headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
		}

		req := createReq.handleJsonRequest(t)
		resp, err := client.Do(req)
		if err != nil {
			return nil, err
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusCreated {
			return nil, fmt.Errorf("expected 201, got %d", resp.StatusCode)
		}

		var createResp refApp.ServerCreateLegislator_Output
		err = json.NewDecoder(resp.Body).Decode(&createResp)
		return &createResp, err
	}

	t.Run("Create", func(t *testing.T) {
		tests := []testCase{
			{
				"Create Legislator Successfully",
				testRequest{
					method: http.MethodPost,
					path:   "/legislators",
					body: refApp.ServerCreateLegislator_Input{
						LegislatorId: legislatorID,
						Name:         "Senator Smith",
						District:     "WA-SD-01",
						Party:        "Independent",
						Role:         "Senator",
						State:        "WA",
						Legislature:  "US",
						Address:      stringPtr("123 Capitol St"),
						Phone:        stringPtr("+12065551234"),
					},
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusCreated,
					body:   &refApp.ServerCreateLegislator_Output{},
				},
				nil,
			},
			{
				"Create Legislator with Duplicate ID",
				testRequest{
					method: http.MethodPost,
					path:   "/legislators",
					body: refApp.ServerCreateLegislator_Input{
						LegislatorId: duplicateID,
						Name:         "Senator Jones",
						District:     "CA-SD-01",
						Party:        "Democrat",
						Role:         "Senator",
						State:        "CA",
						Legislature:  "US",
					},
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusConflict,
				},
				nil,
			},
			{
				"Create Legislator with Missing Required Fields",
				testRequest{
					method: http.MethodPost,
					path:   "/legislators",
					body: refApp.ServerCreateLegislator_Input{
						LegislatorId: 98765,
						Name:         "Representative Missing",
						// Missing required fields like District, Party, Role, State, Legislature
					},
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusUnprocessableEntity,
				},
				nil,
			},
			{
				"Create Legislator with Invalid Phone",
				testRequest{
					method: http.MethodPost,
					path:   "/legislators",
					body: refApp.ServerCreateLegislator_Input{
						LegislatorId: 98766,
						Name:         "Representative Invalid",
						District:     "District 7",
						Party:        "Independent",
						Role:         "Representative",
						State:        "Oregon",
						Legislature:  "State House",
						Phone:        stringPtr("555-1234"), // Invalid format
					},
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusUnprocessableEntity,
				},
				nil,
			},
			{
				"Create Legislator without API Key",
				testRequest{
					method: http.MethodPost,
					path:   "/legislators",
					body: refApp.ServerCreateLegislator_Input{
						LegislatorId: 98767,
						Name:         "Representative Unauthorized",
						District:     "WA-SD-02",
						Party:        "Independent",
						Role:         "Representative",
						State:        "WA",
						Legislature:  "US",
					},
				},
				testResponse{
					status: http.StatusUnauthorized,
				},
				nil,
			},
			{
				"Create Legislator with Invalid API Key",
				testRequest{
					method: http.MethodPost,
					path:   "/legislators",
					body: refApp.ServerCreateLegislator_Input{
						LegislatorId: 98768,
						Name:         "Representative Invalid Key",
						District:     "WA-SD-03",
						Party:        "Independent",
						Role:         "Representative",
						State:        "WA",
						Legislature:  "US",
					},
					headers: map[string]string{"Authorization": "Bearer INVALID_API_KEY"},
				},
				testResponse{
					status: http.StatusUnauthorized,
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
	})

	t.Run("Get", func(t *testing.T) {
		// Create a test legislator for retrieval tests
		testLegislator, err := createTestLegislator(99999, "Senator Test")
		assert.NoError(t, err, "Failed to create test legislator")
		assert.NotEmpty(t, testLegislator.Handle, "Created legislator should have a handle")

		tests := []struct {
			name     string
			path     string
			headers  map[string]string
			expected int
		}{
			{
				"Get Legislator By ID",
				"/legislators?legislatorId=99999",
				map[string]string{"Authorization": "Bearer " + adminApiKey},
				http.StatusOK,
			},
			{
				"Get Legislator That Doesn't Exist",
				"/legislators?legislatorId=88888",
				map[string]string{"Authorization": "Bearer " + adminApiKey},
				http.StatusNotFound,
			},
			{
				"Get Legislator With Invalid ID Format",
				"/legislators?legislatorId=invalid",
				map[string]string{"Authorization": "Bearer " + adminApiKey},
				http.StatusBadRequest,
			},
			{
				"Get Legislator Without Parameters",
				"/legislators",
				map[string]string{"Authorization": "Bearer " + adminApiKey},
				http.StatusBadRequest,
			},
			{
				"Get Legislator Using Handle",
				fmt.Sprintf("/legislators?handle=%s", testLegislator.Handle),
				map[string]string{"Authorization": "Bearer " + adminApiKey},
				http.StatusOK,
			},
			{
				"Get Legislator Using Invalid Handle",
				"/legislators?handle=invalid-handle",
				map[string]string{"Authorization": "Bearer " + adminApiKey},
				http.StatusNotFound,
			},
		}

		for _, tc := range tests {
			t.Run(tc.name, func(t *testing.T) {
				req, err := http.NewRequestWithContext(
					context.Background(),
					http.MethodGet,
					baseUrl+tc.path,
					nil,
				)
				assert.NoError(t, err, "Failed to create HTTP request")

				if tc.headers != nil {
					for k, v := range tc.headers {
						req.Header.Set(k, v)
					}
				}

				resp, err := client.Do(req)
				assert.NoError(t, err, "HTTP request failed")
				defer resp.Body.Close()

				assert.Equal(t, tc.expected, resp.StatusCode)

				if resp.StatusCode == http.StatusOK {
					var profile refApp.LegislatorProfile
					err := json.NewDecoder(resp.Body).Decode(&profile)
					assert.NoError(t, err, "Failed to decode response")
					assert.NotEmpty(t, profile.Name, "Legislator name should not be empty")
				}
			})
		}
	})

	t.Run("Update", func(t *testing.T) {
		_, err := createTestLegislator(updateID, "Senator Original")
		assert.NoError(t, err, "Failed to create test legislator for updates")

		tests := []testCase{
			{
				"Update Legislator Successfully - Handle Only",
				testRequest{
					method: http.MethodPut,
					path:   "/legislators",
					body: refApp.LegislatorUpdateProfile_Input{
						LegislatorId: updateID,
						Handle:       stringPtr("updated-handle.referendumapp.com"),
					},
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusOK,
				},
				nil,
			},
			{
				"Update Legislator Successfully - Name Only",
				testRequest{
					method: http.MethodPut,
					path:   "/legislators",
					body: refApp.LegislatorUpdateProfile_Input{
						LegislatorId: updateID,
						Name:         stringPtr("Senator Updated Name"),
					},
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusOK,
				},
				nil,
			},
			{
				"Update Legislator Successfully - Address Only",
				testRequest{
					method: http.MethodPut,
					path:   "/legislators",
					body: refApp.LegislatorUpdateProfile_Input{
						LegislatorId: updateID,
						Address:      stringPtr("999 Updated Capitol Ave"),
					},
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusOK,
				},
				nil,
			},
			{
				"Update Legislator Successfully - Multiple Fields",
				testRequest{
					method: http.MethodPut,
					path:   "/legislators",
					body: refApp.LegislatorUpdateProfile_Input{
						LegislatorId: updateID,
						Handle:       stringPtr("multi-update.referendumapp.com"),
						Name:         stringPtr("Senator Multi Update"),
						Address:      stringPtr("888 Multi Update St"),
					},
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusOK,
				},
				nil,
			},
			{
				"Update Non-existent Legislator",
				testRequest{
					method: http.MethodPut,
					path:   "/legislators",
					body: refApp.LegislatorUpdateProfile_Input{
						LegislatorId: 999999,
						Name:         stringPtr("NonExistent"),
					},
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusNotFound,
				},
				nil,
			},
			{
				"Update with Invalid Handle",
				testRequest{
					method: http.MethodPut,
					path:   "/legislators",
					body: refApp.LegislatorUpdateProfile_Input{
						LegislatorId: updateID,
						Handle:       stringPtr("invalid_handle"),
					},
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusUnprocessableEntity,
				},
				nil,
			},
			{
				"Update with Missing Legislator ID",
				testRequest{
					method: http.MethodPut,
					path:   "/legislators",
					body: refApp.LegislatorUpdateProfile_Input{
						Name: stringPtr("Missing ID"),
					},
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusUnprocessableEntity,
				},
				nil,
			},
			{
				"Update with No Fields to Update",
				testRequest{
					method: http.MethodPut,
					path:   "/legislators",
					body: refApp.LegislatorUpdateProfile_Input{
						LegislatorId: updateID,
					},
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusOK, // Should succeed even with no fields to update
				},
				nil,
			},
			{
				"Update Legislator without API Key",
				testRequest{
					method: http.MethodPut,
					path:   "/legislators",
					body: refApp.LegislatorUpdateProfile_Input{
						LegislatorId: updateID,
						Name:         stringPtr("Unauthorized Update"),
					},
					// No Authorization header
				},
				testResponse{
					status: http.StatusUnauthorized,
				},
				nil,
			},
			{
				"Update Legislator with Invalid API Key",
				testRequest{
					method: http.MethodPut,
					path:   "/legislators",
					body: refApp.LegislatorUpdateProfile_Input{
						LegislatorId: updateID,
						Name:         stringPtr("Invalid Key Update"),
					},
					headers: map[string]string{"Authorization": "Bearer INVALID_API_KEY"},
				},
				testResponse{
					status: http.StatusUnauthorized,
				},
				nil,
			},
		}

		for _, tc := range tests {
			t.Run(tc.name, func(t *testing.T) {
				req := tc.request.handleJsonRequest(t)
				status := tc.response.getResponse(t, req)

				if status == http.StatusOK {
					updateReq := tc.request.body.(refApp.LegislatorUpdateProfile_Input)
					getReq, err := http.NewRequestWithContext(
						context.Background(),
						http.MethodGet,
						baseUrl+fmt.Sprintf("/legislators?legislatorId=%d", updateReq.LegislatorId),
						nil,
					)
					assert.NoError(t, err, "Failed to create GET request")
					getReq.Header.Set("Authorization", "Bearer "+adminApiKey)

					getResp, err := client.Do(getReq)
					assert.NoError(t, err, "Failed to fetch updated legislator")
					defer getResp.Body.Close()

					if getResp.StatusCode == http.StatusOK {
						var profile refApp.LegislatorProfile
						err := json.NewDecoder(getResp.Body).Decode(&profile)
						assert.NoError(t, err, "Failed to decode updated legislator")

						if updateReq.Name != nil {
							assert.Equal(t, *updateReq.Name, profile.Name, "Name should be updated")
						}
						if updateReq.Address != nil {
							assert.Equal(t, *updateReq.Address, *profile.Address, "Address should be updated")
						}
					}
				}
			})
		}
	})

	t.Run("Delete", func(t *testing.T) {
		_, err := createTestLegislator(deleteID, "Senator ToDelete")
		assert.NoError(t, err, "Failed to create test legislator for deletion")

		tests := []testCase{
			{
				"Delete Legislator By ID",
				testRequest{
					method:  http.MethodDelete,
					path:    "/legislators?legislatorId=77777",
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusOK,
				},
				nil,
			},
			{
				"Delete Non-existent Legislator",
				testRequest{
					method:  http.MethodDelete,
					path:    "/legislators?legislatorId=88888",
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusNotFound,
				},
				nil,
			},
			{
				"Delete Legislator with Invalid ID Format",
				testRequest{
					method:  http.MethodDelete,
					path:    "/legislators?legislatorId=invalid",
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusBadRequest,
				},
				nil,
			},
			{
				"Delete Legislator Without Parameters",
				testRequest{
					method:  http.MethodDelete,
					path:    "/legislators",
					headers: map[string]string{"Authorization": "Bearer " + adminApiKey},
				},
				testResponse{
					status: http.StatusBadRequest,
				},
				nil,
			},
			{
				"Delete Legislator without API Key",
				testRequest{
					method: http.MethodDelete,
					path:   "/legislators?legislatorId=99998",
					// No Authorization header
				},
				testResponse{
					status: http.StatusUnauthorized,
				},
				nil,
			},
			{
				"Delete Legislator with Invalid API Key",
				testRequest{
					method:  http.MethodDelete,
					path:    "/legislators?legislatorId=99997",
					headers: map[string]string{"Authorization": "Bearer INVALID_API_KEY"},
				},
				testResponse{
					status: http.StatusUnauthorized,
				},
				nil,
			},
		}

		for _, tc := range tests {
			t.Run(tc.name, func(t *testing.T) {
				req := tc.request.handleJsonRequest(t)
				sc := tc.response.getResponse(t, req)

				if sc == http.StatusOK {
					verificationReq := testRequest{
						method:  http.MethodGet,
						path:    tc.request.path,
						headers: tc.request.headers,
					}

					verificationResp := testResponse{
						status: http.StatusNotFound,
					}

					req := verificationReq.handleJsonRequest(t)
					actualStatus := verificationResp.getResponse(t, req)

					if actualStatus == http.StatusNotFound {
						t.Logf("Verified deletion: Legislator %d returns 404 after deletion", legislatorID)
					}
				}
			})
		}
	})
}

func stringPtr(s string) *string {
	return &s
}
