package server

import (
	"database/sql"
	"net/http"

	"github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

func (s *Server) handleLogin(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	if err := r.ParseForm(); err != nil {
		s.log.ErrorContext(ctx, "Invalid form", "error", err)
		refErr.BadRequest("Faild to parse form data from request").WriteResponse(w)
		return
	}

	login := referendumapp.ServerCreateSession_Input{
		GrantType: r.Form.Get("grantType"),
		Username:  r.Form.Get("email"),
		Password:  r.Form.Get("password"),
	}

	if err := util.Validate.Struct(login); err != nil {
		apiErrs := util.HandleFieldError(err, s.log)
		refErr.WriteFieldErrors(w, apiErrs)
		return
	}

	defaultErr := refErr.FieldError{Field: "email", Message: "Email or password not found"}
	user, err := s.db.AuthenticateUser(ctx, login.Username)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to authenticate user", "error", err)
		if err == sql.ErrNoRows {
			defaultErr.NotFound().WriteResponse(w)
			return
		}
		refErr.InternalServer().WriteResponse(w)
		return
	}

	if ok, verr := util.VerifyPassword(login.Password, user.HashedPassword.String); verr != nil {
		s.log.ErrorContext(ctx, "Error verifying password", "error", verr)
		refErr.InternalServer().WriteResponse(w)
	} else if !ok {
		s.log.Error("Invalid login password")
		defaultErr.NotFound().WriteResponse(w)
	}

	accessToken, err := s.jwt.CreateToken(user.Did, util.Access)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to create access token", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}
	refreshToken, err := s.jwt.CreateToken(user.Did, util.Refresh)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to create refresh token", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	resp := referendumapp.ServerCreateSession_Output{
		Did:          user.Did,
		Handle:       user.Handle.String,
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    s.jwt.AuthScheme,
	}
	util.Encode(w, http.StatusOK, s.log, resp)
}

func (s *Server) handleRefresh(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Extract the refresh token from the request
	var req referendumapp.ServerRefreshSession_Input
	if err := util.DecodeAndValidate(w, r, s.log, &req); err != nil {
		return
	}

	// Parse and validate the token
	token, err := s.jwt.DecodeJWT(req.RefreshToken)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to decode refresh token", "error", err)
		refErr.Unauthorized("Invalid refresh token").WriteResponse(w)
		return
	}

	email, err := util.ValidateToken(token, util.Refresh)
	if err != nil {
		s.log.ErrorContext(ctx, "Token validation failed", "error", err)
		refErr.BadRequest("Failed to validate refresh token").WriteResponse(w)
		return
	}

	user, err := s.db.AuthenticateUser(ctx, email)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to lookup user", "error", err)
		if err == sql.ErrNoRows {
			refErr.NotFound(email, "user ID").WriteResponse(w)
			return
		}
		refErr.BadRequest("Failed to find user with refresh token").WriteResponse(w)
		return
	}

	accessToken, err := s.jwt.CreateToken(user.Did, util.Access)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to create access token", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}
	refreshToken, err := s.jwt.CreateToken(user.Did, util.Refresh)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to create refresh token", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	resp := referendumapp.ServerRefreshSession_Output{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    s.jwt.AuthScheme,
	}
	util.Encode(w, http.StatusOK, s.log, resp)
}
