package pds

import (
	"context"
	"errors"
	"net/http"

	"github.com/golang-jwt/jwt/v5"

	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

// Authorize a request based on the JWT included in the request
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

		uid, did, err := util.ValidateToken(token, util.Access)
		if err != nil {
			p.log.ErrorContext(requestCtx, "Failed validate access token", "error", err)
			refErr.BadRequest("Invalid token type for access token").WriteResponse(w)
			return
		}

		didCtx := context.WithValue(requestCtx, p.jwt.DidKey, did)
		ctx := context.WithValue(didCtx, p.jwt.SubjectKey, uid)

		next.ServeHTTP(w, r.WithContext(ctx))
	})
}
