package server

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"strings"

	"github.com/referendumApp/referendumServices/internal/domain/common"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

func (s *Server) getAndValidateUser(w http.ResponseWriter, ctx context.Context) (*common.User, bool) {
	user, ok := ctx.Value(s.jwtConfig.ContextKey).(*common.User)
	if !ok {
		s.log.Error("Invalid user in request context")
		refErr.Unauthorized("Unauthorized user").WriteResponse(w)
	}
	return user, ok
}

// func (s *Server) getAndValidateTx(w http.ResponseWriter, ctx context.Context) (pgx.Tx, bool) {
// 	tx, ok := ctx.Value(TxCtxKey).(pgx.Tx)
// 	if !ok {
// 		s.log.Error("Transaction required for this endpoint handler")
// 		refErr.InternalServer().WriteResponse(w)
// 	}
// 	return tx, ok
// }

// Encode and validate the response body
func encode[T any](w http.ResponseWriter, status int, v T) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("Error encoding response: %v", err)
		http.Error(w, "Failed to generate response", http.StatusInternalServerError)
	}
}

// Decode and validate the request body
func (s *Server) decodeAndValidate(r *http.Request, v common.Validator) *refErr.APIError {
	if err := json.NewDecoder(r.Body).Decode(v); err != nil {
		s.log.Error("Failed to decode request body", "error", err)
		return refErr.UnproccessableEntity("invalid request body")
	}

	if err := v.Validate(r.Context()); err != nil {
		s.log.Error("Request validation failed", "error", err)
		return err
	}

	return nil
}

func getClientIdentifier(r *http.Request) string {
	// Get the real IP address
	ip := r.Header.Get("X-Forwarded-For")
	if ip == "" {
		ip = r.Header.Get("X-Real-IP")
	}
	if ip == "" {
		ip = r.RemoteAddr
	}

	// If there are multiple IPs in X-Forwarded-For, use the first one
	if idx := strings.Index(ip, ","); idx != -1 {
		ip = ip[:idx]
	}

	// Get the user agent
	userAgent := r.UserAgent()

	// Combine them into an identifier
	ident := ip + "-" + userAgent

	return ident
}
