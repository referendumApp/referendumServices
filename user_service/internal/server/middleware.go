package server

import (
	"context"
	"errors"
	"fmt"
	"log"
	"net/http"
	"regexp"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

type UserIDKey string

const UserIdKey UserIDKey = "userId"

var bearerRegex = regexp.MustCompile(`Bearer\s+(.*)`)

// Extract the JWT from the Authorization request header
func extractToken(r *http.Request) string {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return authHeader
	}

	match := bearerRegex.FindStringSubmatch(authHeader)
	if len(match) > 1 {
		return strings.TrimSpace(match[1])
	}

	return ""
}

// Decode and validate the JWT and get the claims
func decodeJWT(tokenString string, secretKey []byte) (jwt.MapClaims, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (any, error) {
		// Validate the algorithm is what we expect
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, errors.New("unexpected signing method")
		}

		// Return the secret key used to sign the token
		return secretKey, nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		return claims, nil
	}

	return nil, errors.New("failed to validate token")
}

// Authorize a request based on the JWT included in the request
func (s *Server) authorizeUser(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestCtx := r.Context()

		accessToken := extractToken(r)
		if accessToken == "" {
			http.Error(w, "Token not found", http.StatusUnauthorized)
			return
		}

		claims, err := decodeJWT(accessToken, s.secretKey)
		if err != nil {
			http.Error(w, fmt.Errorf("invalid access token: %s", err).Error(), http.StatusUnauthorized)
			return
		}

		if tokenType, ok := claims["type"].(string); !ok || tokenType != "access" {
			http.Error(w, "Invalid token type for access token", http.StatusUnauthorized)
			return
		}

		// Include the email in the request context that will be passed down to the handlers
		email, ok := claims["sub"].(string)
		if !ok {
			http.Error(w, "Missing email in access token", http.StatusUnauthorized)
			return
		}

		userId, err := s.db.GetUserId(requestCtx, email)
		if err != nil {
			http.Error(w, err.Error(), http.StatusUnauthorized)
			return
		}

		ctx := context.WithValue(requestCtx, UserIdKey, userId)
		r = r.WithContext(ctx)

		next.ServeHTTP(w, r)
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

// Log metadata and status for the request
func logRequest(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		startTime := time.Now()

		// Wrap the ResponseWriter so we can include the status code in our logs
		rw := &CustomResponseWriter{
			ResponseWriter: w,
			StatusCode:     http.StatusOK,
		}

		// Log request details
		log.Printf(
			"REQUEST: %s %s %s",
			r.Method,
			r.URL.Path,
			r.RemoteAddr,
		)

		// Call the next handler
		next.ServeHTTP(rw, r)

		// Log completion time
		duration := time.Since(startTime)
		log.Printf(
			"COMPLETED: %s %s - status %d in %v",
			r.Method,
			r.URL.Path,
			rw.StatusCode,
			duration,
		)
	})
}
