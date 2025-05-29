package pds

import (
	"context"
	"errors"
	"fmt"
	"net/http"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

// AuthResult holds authentication results
type AuthResult struct {
	Aid atp.Aid
	Did string
}

// AuthorizeSystem validates API keys for system users
func (p *PDS) AuthorizeSystem(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		result, err := p.trySystemAuth(r)
		if err != nil {
			p.writeAuthError(w, r, "System authentication failed", err)
			return
		}

		ctx := p.setAuthContext(r.Context(), result)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// AuthorizeUser validates JWT tokens for app users
func (p *PDS) AuthorizeUser(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		result, err := p.tryUserAuth(r)
		if err != nil {
			p.writeAuthError(w, r, "User authentication failed", err)
			return
		}

		ctx := p.setAuthContext(r.Context(), result)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// AuthorizeSystemOrUser validates either system API keys or user JWT tokens
func (p *PDS) AuthorizeSystemOrUser(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		result, err := p.tryUserAuth(r)
		if err == nil {
			ctx := p.setAuthContext(r.Context(), result)
			next.ServeHTTP(w, r.WithContext(ctx))
			return
		}

		result, err = p.trySystemAuth(r)
		if err == nil {
			ctx := p.setAuthContext(r.Context(), result)
			next.ServeHTTP(w, r.WithContext(ctx))
			return
		}

		p.writeAuthError(w, r, "Authentication failed - no valid system API key or user token found", nil)
	})
}

// trySystemAuth attempts system authentication
func (p *PDS) trySystemAuth(r *http.Request) (*AuthResult, error) {
	// TODO: Implement when system auth is ready
	// token, err := p.extractBearerToken(r)
	// if err != nil {
	//     return nil, fmt.Errorf("bearer token extraction failed: %w", err)
	// }
	//
	// aid, did, err := util.ValidateApiKey(token)
	// if err != nil {
	//     return nil, fmt.Errorf("API key validation failed: %w", err)
	// }
	//
	// return &AuthResult{Aid: aid, Did: did}, nil

	return &AuthResult{Aid: 1, Did: "1"}, nil
}

// tryUserAuth attempts user authentication
func (p *PDS) tryUserAuth(r *http.Request) (*AuthResult, error) {
	accessToken := p.jwt.ExtractToken(r)
	if accessToken == "" {
		return nil, errors.New("no JWT token found")
	}

	token, err := p.jwt.DecodeJWT(accessToken)
	if err != nil {
		return nil, fmt.Errorf("JWT decode failed: %w", err)
	}

	aid, did, err := util.ValidateToken(token, util.Access)
	if err != nil {
		return nil, fmt.Errorf("token validation failed: %w", err)
	}

	return &AuthResult{Aid: aid, Did: did}, nil
}

// setAuthContext sets the DID and Subject context values
func (p *PDS) setAuthContext(ctx context.Context, result *AuthResult) context.Context {
	didCtx := context.WithValue(ctx, p.jwt.DidKey, result.Did)
	return context.WithValue(didCtx, p.jwt.SubjectKey, result.Aid)
}

// writeAuthError logs the error and writes an unauthorized response
func (p *PDS) writeAuthError(w http.ResponseWriter, r *http.Request, message string, err error) {
	if err != nil {
		p.log.ErrorContext(r.Context(), message, "error", err)
	} else {
		p.log.ErrorContext(r.Context(), message)
	}
	refErr.Unauthorized(message).WriteResponse(w)
}
