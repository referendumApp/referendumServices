package service

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"strings"
	"time"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

// CustomResponseWriter wrapper around 'http.ResponseWriter' to track the status code of the request
type CustomResponseWriter struct {
	http.ResponseWriter
	StatusCode int
}

// WriteHeader wrapper around 'WriteHeader' method to write the status code
func (rw *CustomResponseWriter) WriteHeader(code int) {
	rw.StatusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Hijack required for websockets
func (rw *CustomResponseWriter) Hijack() (net.Conn, *bufio.ReadWriter, error) {
	if hijacker, ok := rw.ResponseWriter.(http.Hijacker); ok {
		return hijacker.Hijack()
	}
	return nil, nil, fmt.Errorf("underlying ResponseWriter does not implement http.Hijacker")
}

func getOrCreateCustomWriter(w http.ResponseWriter) *CustomResponseWriter {
	if customWriter, ok := w.(*CustomResponseWriter); ok {
		return customWriter
	}
	return &CustomResponseWriter{
		ResponseWriter: w,
		StatusCode:     http.StatusOK,
	}
}

func (s *Service) logRequest(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		startTime := time.Now()

		// Wrap the ResponseWriter so we can include the status code in our logs
		rw := getOrCreateCustomWriter(w)

		// Log request details
		s.log.InfoContext(
			r.Context(),
			"Request started",
			"method",
			r.Method,
			"path",
			r.URL.Path,
			"address",
			r.RemoteAddr,
		)

		next.ServeHTTP(rw, r)

		duration := fmt.Sprintf("%d ms", time.Since(startTime).Milliseconds())
		s.log.InfoContext(
			r.Context(),
			"Request completed",
			"method",
			r.Method,
			"path",
			r.URL.Path,
			"status",
			rw.StatusCode,
			"duration",
			duration,
		)
	})
}

func withCancellation(parent context.Context, ch <-chan struct{}) (context.Context, context.CancelFunc) {
	ctx, cancel := context.WithCancel(parent)
	go func() {
		select {
		case <-ch:
			cancel()
		case <-ctx.Done():
		}
	}()
	return ctx, cancel
}

func (s *Service) gracefulShutdown(next http.Handler, cancelCh <-chan struct{}) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := withCancellation(r.Context(), cancelCh)
		defer cancel()
		r = r.WithContext(ctx)
		next.ServeHTTP(w, r)
	})
}

func (s *Service) requestTimeout(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.TimeoutHandler(next, 15*time.Second, "Request timed out").ServeHTTP(w, r)
	})
}

// extractBearerToken extracts and validates the Bearer token from the Authorization header
func (s *Service) extractBearerToken(r *http.Request) (string, error) {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return "", errors.New("missing Authorization header")
	}

	const bearerPrefix = "Bearer "
	if !strings.HasPrefix(authHeader, bearerPrefix) {
		return "", errors.New("invalid Authorization header format")
	}

	token := strings.TrimSpace(authHeader[len(bearerPrefix):])
	if token == "" {
		return "", errors.New("empty token")
	}

	return token, nil
}

// setContextFromAuth sets the DID and Subject context values from auth results
func (s *Service) setContextFromAuth(ctx context.Context, aid *atp.Aid, did *string) context.Context {
	var aidValue atp.Aid
	var didValue string

	if aid != nil {
		aidValue = *aid
	}
	if did != nil {
		didValue = *did
	}

	didCtx := context.WithValue(ctx, util.DidKey, didValue)
	return context.WithValue(didCtx, util.SubjectKey, aidValue)
}

// writeUnauthorizedError logs the error and writes an unauthorized response
func (s *Service) writeUnauthorizedError(w http.ResponseWriter, r *http.Request, message string, err error) {
	if err != nil {
		s.log.ErrorContext(r.Context(), message, "error", err)
	} else {
		s.log.ErrorContext(r.Context(), message)
	}
	refErr.Unauthorized(message).WriteResponse(w)
}

// AuthorizeUser validates regular user tokens only (delegates to PDS)
func (s *Service) AuthorizeUser(next http.Handler) http.Handler {
	return s.pds.AuthorizeUser(next)
}

// AuthorizeSystem validates system user tokens only
func (s *Service) AuthorizeSystem(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token, err := s.extractBearerToken(r)
		if err != nil {
			s.writeUnauthorizedError(w, r, err.Error(), nil)
			return
		}

		aid, did, err := util.ValidateApiKey(token)
		if err != nil {
			s.writeUnauthorizedError(w, r, "Invalid API key", err)
			return
		}

		ctx := s.setContextFromAuth(r.Context(), aid, did)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// AuthorizeSystemOrUser validates both system user and regular user tokens
func (s *Service) AuthorizeSystemOrUser(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token, err := s.extractBearerToken(r)
		if err != nil {
			s.writeUnauthorizedError(w, r, err.Error(), nil)
			return
		}

		// Try API key validation first
		if aid, did, err := util.ValidateApiKey(token); err == nil {
			s.log.InfoContext(r.Context(), "Authenticated as system user")
			ctx := s.setContextFromAuth(r.Context(), aid, did)
			next.ServeHTTP(w, r.WithContext(ctx))
			return
		}

		s.log.InfoContext(r.Context(), "API key validation failed, trying user token validation")

		authCapture := &authResponseCapture{ResponseWriter: w}

		s.AuthorizeUser(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authCapture.authSucceeded = true
			next.ServeHTTP(w, r)
		})).ServeHTTP(authCapture, r)

		if !authCapture.authSucceeded && !authCapture.responseWritten {
			s.writeUnauthorizedError(w, r, "Invalid token", nil)
		}
	})
}

// authResponseCapture captures authentication state and response status
type authResponseCapture struct {
	http.ResponseWriter
	authSucceeded   bool
	responseWritten bool
}

func (c *authResponseCapture) WriteHeader(statusCode int) {
	c.responseWritten = true
	c.ResponseWriter.WriteHeader(statusCode)
}

func (c *authResponseCapture) Write(data []byte) (int, error) {
	c.responseWritten = true
	return c.ResponseWriter.Write(data)
}
