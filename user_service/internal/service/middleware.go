package service

import (
	"bufio"
	"context"
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

// AuthorizeSystemUser validates system user tokens only
func (s *Service) AuthorizeSystemUser(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestCtx := r.Context()

		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			s.log.ErrorContext(requestCtx, "Missing Authorization header")
			refErr.Unauthorized("Missing Authorization header").WriteResponse(w)
			return
		}

		const bearerPrefix = "Bearer "
		if !strings.HasPrefix(authHeader, bearerPrefix) {
			s.log.ErrorContext(requestCtx, "Invalid Authorization header format")
			refErr.Unauthorized("Invalid Authorization header format").WriteResponse(w)
			return
		}

		token := strings.TrimSpace(authHeader[len(bearerPrefix):])
		if token == "" {
			s.log.ErrorContext(requestCtx, "Empty token in Authorization header")
			refErr.Unauthorized("Empty token").WriteResponse(w)
			return
		}

		aid, did, err := util.ValidateApiKey(token)
		if err != nil {
			s.log.ErrorContext(requestCtx, "Failed to validate API key", "error", err)
			refErr.Unauthorized("Invalid API key").WriteResponse(w)
			return
		}

		var aidValue atp.Aid
		var didValue string
		if aid != nil {
			aidValue = *aid
		}
		if did != nil {
			didValue = *did
		}

		didCtx := context.WithValue(requestCtx, util.DidKey, didValue)
		ctx := context.WithValue(didCtx, util.SubjectKey, aidValue)

		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// AuthorizeUser validates regular user tokens only (delegates to PDS)
func (s *Service) AuthorizeUser(next http.Handler) http.Handler {
	return s.pds.AuthorizeUser(next)
}

// AuthorizeAdminOrUser validates both system user and regular user tokens
func (s *Service) AuthorizeAdminOrUser(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestCtx := r.Context()

		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			s.log.ErrorContext(requestCtx, "Missing Authorization header")
			refErr.Unauthorized("Missing Authorization header").WriteResponse(w)
			return
		}

		const bearerPrefix = "Bearer "
		if !strings.HasPrefix(authHeader, bearerPrefix) {
			s.log.ErrorContext(requestCtx, "Invalid Authorization header format")
			refErr.Unauthorized("Invalid Authorization header format").WriteResponse(w)
			return
		}

		token := strings.TrimSpace(authHeader[len(bearerPrefix):])
		if token == "" {
			s.log.ErrorContext(requestCtx, "Empty token in Authorization header")
			refErr.Unauthorized("Empty token").WriteResponse(w)
			return
		}

		// First try to validate as API key (system user)
		if aid, did, err := util.ValidateApiKey(token); err == nil {
			s.log.InfoContext(requestCtx, "Authenticated as system user")

			// Set context values (handle pointer dereferencing if needed)
			var aidValue atp.Aid
			var didValue string

			if aid != nil {
				aidValue = *aid
			}
			if did != nil {
				didValue = *did
			}

			didCtx := context.WithValue(requestCtx, util.DidKey, didValue)
			ctx := context.WithValue(didCtx, util.SubjectKey, aidValue)

			next.ServeHTTP(w, r.WithContext(ctx))
			return
		}

		// If API key validation fails, try user token validation through PDS
		s.log.InfoContext(requestCtx, "API key validation failed, trying user token validation")

		// Create a custom response writer to capture the response from PDS auth
		customWriter := &authResponseCapture{
			ResponseWriter: w,
			authSucceeded:  false,
		}

		// Try PDS user authentication
		s.pds.AuthorizeUser(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// If we reach here, PDS authentication succeeded
			customWriter.authSucceeded = true
			next.ServeHTTP(w, r)
		})).ServeHTTP(customWriter, r)

		// If PDS auth also failed and no response was written, write unauthorized
		if !customWriter.authSucceeded && !customWriter.responseWritten {
			s.log.ErrorContext(requestCtx, "Both API key and user token validation failed")
			refErr.Unauthorized("Invalid token").WriteResponse(w)
		}
	})
}

// authResponseCapture captures whether authentication succeeded and if a response was written
type authResponseCapture struct {
	http.ResponseWriter
	authSucceeded   bool
	responseWritten bool
}

func (arc *authResponseCapture) WriteHeader(statusCode int) {
	arc.responseWritten = true
	arc.ResponseWriter.WriteHeader(statusCode)
}

func (arc *authResponseCapture) Write(data []byte) (int, error) {
	arc.responseWritten = true
	return arc.ResponseWriter.Write(data)
}
