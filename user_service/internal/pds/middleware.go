package pds

import (
	"context"
	"errors"
	"net/http"
	"strings"

	"github.com/golang-jwt/jwt/v5"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

// AuthorizeUser validate a request based on the JWT included in the request
func (p *PDS) AuthorizeUser(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestCtx := r.Context()

		accessToken := p.jwt.ExtractToken(r)
		if accessToken == "" {
			refErr.Unauthorized("Token not found").WriteResponse(w)
			return
		}

		token, err := p.jwt.DecodeJWT(accessToken)
		if err != nil {
			p.log.ErrorContext(requestCtx, "Failed to decode JWT", "error", err)
			if errors.Is(err, jwt.ErrTokenExpired) {
				refErr.Unauthorized("JWT expired").WriteResponse(w)
				return
			}

			refErr.BadRequest("Invalid token").WriteResponse(w)
			return
		}

		aid, did, err := util.ValidateToken(token, util.Access)
		if err != nil {
			p.log.ErrorContext(requestCtx, "Failed validate access token", "error", err)
			refErr.BadRequest("Invalid token type for access token").WriteResponse(w)
			return
		}

		didCtx := context.WithValue(requestCtx, p.jwt.DidKey, did)
		ctx := context.WithValue(didCtx, p.jwt.SubjectKey, aid)

		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// extractBearerToken extracts and validates the Bearer token from the Authorization header
func (p *PDS) extractBearerToken(r *http.Request) (string, error) {
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
func (p *PDS) setContextFromAuth(ctx context.Context, aid *atp.Aid, did *string) context.Context {
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
func (p *PDS) writeUnauthorizedError(w http.ResponseWriter, r *http.Request, message string, err error) {
	if err != nil {
		p.log.ErrorContext(r.Context(), message, "error", err)
	} else {
		p.log.ErrorContext(r.Context(), message)
	}
	refErr.Unauthorized(message).WriteResponse(w)
}

// AuthorizeSystemUser validates system user tokens only
func (p *PDS) AuthorizeSystemUser(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token, err := p.extractBearerToken(r)
		if err != nil {
			p.writeUnauthorizedError(w, r, err.Error(), nil)
			return
		}

		aid, did, err := util.ValidateApiKey(token)
		if err != nil {
			p.writeUnauthorizedError(w, r, "Invalid API key", err)
			return
		}

		ctx := p.setContextFromAuth(r.Context(), aid, did)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// AuthorizeAdminOrUser validates both system user and regular user tokens
func (p *PDS) AuthorizeAdminOrUser(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token, err := p.extractBearerToken(r)
		if err != nil {
			p.writeUnauthorizedError(w, r, err.Error(), nil)
			return
		}

		// Try API key validation first
		if aid, did, err := util.ValidateApiKey(token); err == nil {
			p.log.InfoContext(r.Context(), "Authenticated as system user")
			ctx := p.setContextFromAuth(r.Context(), aid, did)
			next.ServeHTTP(w, r.WithContext(ctx))
			return
		}

		p.log.InfoContext(r.Context(), "API key validation failed, trying user token validation")

		authCapture := &authResponseCapture{ResponseWriter: w}

		p.AuthorizeUser(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authCapture.authSucceeded = true
			next.ServeHTTP(w, r)
		})).ServeHTTP(authCapture, r)

		if !authCapture.authSucceeded && !authCapture.responseWritten {
			p.writeUnauthorizedError(w, r, "Invalid token", nil)
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
