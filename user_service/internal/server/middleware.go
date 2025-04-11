package server

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"time"

	"github.com/golang-jwt/jwt/v5"

	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

// Authorize a request based on the JWT included in the request
func (s *Server) authorizeUser(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestCtx := r.Context()

		accessToken := s.jwt.ExtractToken(r)
		if accessToken == "" {
			refErr.Unauthorized("Token not found").WriteResponse(w)
			return
		}

		token, err := s.jwt.DecodeJWT(accessToken)
		if err != nil {
			s.log.ErrorContext(requestCtx, "Failed to decode JWT", "error", err)
			if errors.Is(err, jwt.ErrTokenExpired) {
				refErr.Unauthorized("JWT expired").WriteResponse(w)
				return
			}

			refErr.BadRequest("Invalid token").WriteResponse(w)
			return
		}

		did, err := util.ValidateToken(token, util.Access)
		if err != nil {
			refErr.BadRequest("Invalid token type for access token").WriteResponse(w)
			return
		}

		per, err := s.db.LookupPersonByDid(requestCtx, did)
		if err != nil {
			s.log.ErrorContext(requestCtx, "Failed to authorize user with DID", "error", err, "DID", did)
			refErr.InternalServer().WriteResponse(w)
			return
		}

		ctx := context.WithValue(requestCtx, s.jwt.ContextKey, per)

		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

type CustomResponseWriter struct {
	http.ResponseWriter
	StatusCode int
}

func (rw *CustomResponseWriter) WriteHeader(code int) {
	rw.StatusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

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

type TransactionCtxKey string

const TxCtxKey TransactionCtxKey = "tx"

func (s *Server) logRequest(next http.Handler) http.Handler {
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
			"urlPath",
			r.URL.Path,
			"address",
			r.RemoteAddr,
		)

		// Call the next handler
		next.ServeHTTP(rw, r)

		// Log completion time
		duration := time.Since(startTime)
		s.log.InfoContext(
			r.Context(),
			"Request completed",
			"method",
			r.Method,
			"urlPath",
			r.URL.Path,
			"status",
			rw.StatusCode,
			"duration",
			duration,
		)
	})
}
