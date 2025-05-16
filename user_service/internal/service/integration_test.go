//go:build integration

package service

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
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

	assert.Equal(t, e.status, resp.StatusCode)

	if e.body != nil && resp.Body != nil && resp.StatusCode < 300 {
		decodeErr := json.NewDecoder(resp.Body).Decode(e.body)
		assert.NoError(t, decodeErr, "Error decoding response body")

		valErr := util.Validate.Struct(e.body)
		assert.NoError(t, valErr, "Error validating response body")
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
			t.Logf("%s: %s", tc.name, tc.request.headers)
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

func TestCreateLegislator(t *testing.T) {
	tests := []testCase{
		{
			"Create Legislator Successfully",
			testRequest{
				method: http.MethodPost,
				path:   "/legislator",
				body: refApp.ServerCreateLegislator_Input{
					LegislatorId: 12345,
					Name:         "Senator Smith",
					District:     "WA-SD-01",
					Party:        "Independent",
					Role:         "Senator",
					State:        "WA",
					Legislature:  "US",
					Address:      stringPtr("123 Capitol St"),
					Phone:        stringPtr("+12065551234"),
				},
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
				path:   "/legislator",
				body: refApp.ServerCreateLegislator_Input{
					LegislatorId: 12345, // Same ID as previous test
					Name:         "Senator Jones",
					District:     "CA-SD-01",
					Party:        "Democrat",
					Role:         "Senator",
					State:        "CA",
					Legislature:  "US",
				},
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
				path:   "/legislator",
				body: refApp.ServerCreateLegislator_Input{
					LegislatorId: 54321,
					Name:         "Representative Missing",
				},
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
				path:   "/legislator",
				body: refApp.ServerCreateLegislator_Input{
					LegislatorId: 54321,
					Name:         "Representative Invalid",
					District:     "District 7",
					Party:        "Independent",
					Role:         "Representative",
					State:        "Oregon",
					Legislature:  "State House",
					Phone:        stringPtr("555-1234"),
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
			status := tc.response.getResponse(t, req)

			if status == http.StatusCreated {
				duplicateReq := testRequest{
					method: http.MethodPost,
					path:   "/legislator",
					body:   tc.request.body,
				}

				req := duplicateReq.handleJsonRequest(t)
				resp, err := client.Do(req)
				assert.NoError(t, err, "HTTP request failed")
				defer resp.Body.Close()

				assert.Equal(
					t,
					http.StatusConflict,
					resp.StatusCode,
					"Expected conflict when creating duplicate legislator",
				)
			}
		})
	}
}

func stringPtr(s string) *string {
	return &s
}
