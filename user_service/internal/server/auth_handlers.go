package server

import (
	"context"
	"database/sql"
	"net/http"
	"strings"

	"github.com/jackc/pgx/v5"

	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	"github.com/referendumApp/referendumServices/internal/domain/auth"
	"github.com/referendumApp/referendumServices/internal/domain/common"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

func (s *Server) validateHandle(ctx context.Context, handle string) *refErr.APIError {
	if !strings.HasSuffix(handle, s.handleSuffix) {
		fieldErr := refErr.FieldError{Field: auth.HANDLE, Message: "Invalid handle format"}
		return fieldErr.Invalid()
	}

	if strings.Contains(strings.TrimSuffix(handle, s.handleSuffix), ".") {
		fieldErr := refErr.FieldError{Field: auth.HANDLE, Message: "Invalid character '.'"}
		return fieldErr.Invalid()
	}

	if exists, err := s.db.UserExists(ctx, "handle", handle); err != nil {
		s.log.ErrorContext(ctx, "Error checking database for user handle", "error", err)
		return refErr.InternalServer()
	} else if exists {
		fieldErr := refErr.FieldError{Field: auth.HANDLE, Message: "Handle already exists"}
		return fieldErr.Conflict()
	}

	return nil
}

func (s *Server) handleSignUp(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// tx, ok := s.getAndValidateTx(w, ctx)
	// if !ok {
	//   return
	// }

	var req auth.SignUpRequest
	if err := s.decodeAndValidate(r, &req); err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.validateHandle(ctx, req.Handle); err != nil {
		s.log.ErrorContext(ctx, "Error validating handle", "error", err)
		err.WriteResponse(w)
		return
	}

	if exists, err := s.db.UserExists(ctx, "email", req.Email); err != nil {
		s.log.ErrorContext(ctx, "Error checking database for user email", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	} else if exists {
		s.log.ErrorContext(ctx, "Email already registered", "user", req.Email)
		fieldErr := refErr.FieldError{Field: auth.EMAIL, Message: "Email already exists"}
		fieldErr.Conflict().WriteResponse(w)
		return
	}
	// if !errors.Is(err, pgx.ErrNoRows) && err != nil {
	// 	s.log.ErrorContext(ctx, "Error checking database for user", "error", err)
	// 	refErr.InternalServer().WriteResponse(w)
	// 	return
	// }

	// // If they haven't been soft deleted then raise an error
	// if !errors.Is(err, pgx.ErrNoRows) && !user.Settings.Deleted {
	// 	s.log.ErrorContext(ctx, "Signup failed: Email already registered", "user", req.Email)
	// 	fieldErr := refErr.FieldError{Field: auth.EMAIL, Message: "Email already exists"}
	// 	fieldErr.Conflict().WriteResponse(w)
	// 	return
	// }

	// If the user doesn't exist then create them
	hashedPassword, err := common.HashPassword(req.Password, common.DefaultParams())
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to hash password", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	// if user == nil {
	var recoveryKey string
	if req.RecoveryKey != nil {
		recoveryKey = *req.RecoveryKey
	}
	if recoveryKey == "" {
		recoveryKey = s.signingKey.Public().DID()
	}

	d, err := s.plc.CreateDID(ctx, s.signingKey, recoveryKey, req.Handle, s.serviceUrl)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to create DID", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	s.log.InfoContext(ctx, "Creating new user", "did", d, "handle", req.Handle)
	user := common.User{
		Name:           req.Name,
		Handle:         req.Handle,
		Email:          req.Email,
		HashedPassword: hashedPassword,
		RecoveryKey:    recoveryKey,
		Did:            d,
		Settings:       &common.UserSettings{Deleted: false},
	}
	// if exists, err := s.db.AuthenticateHandle(ctx, user); err != nil {
	// 	s.log.ErrorContext(ctx, "Failed to authenticate handle", "error", err, "handle", req.Handle)
	// 	refErr.InternalServer().WriteResponse(w)
	// 	return
	// } else if exists {
	// 	s.log.ErrorContext(ctx, "Signup failed: Handle already exists", "handle", user.Handle)
	// 	fieldErr := refErr.FieldError{Field: auth.HANDLE, Message: "Handle already exists"}
	// 	fieldErr.Conflict().WriteResponse(w)
	// 	return
	// }

	if err := s.db.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		newUser, err := database.CreateWithReturningWithTx(ctx, s.db, tx, user, "id")
		if err != nil {
			s.log.ErrorContext(ctx, "Failed to create user", "error", err, "did", d)
			return err
		}

		actor := &atp.Citizen{
			Uid:    newUser.ID,
			Did:    user.Did,
			Handle: sql.NullString{String: req.Handle, Valid: true},
		}

		if err := s.db.CreateWithTx(ctx, tx, actor); err != nil {
			s.log.ErrorContext(ctx, "Failed to create actor", "error", err, "did", d)
			return err
		}

		user.ID = newUser.ID

		return nil
	}); err != nil {
		refErr.InternalServer().WriteResponse(w)
		return
	}

	if err := s.repoman.InitNewActor(ctx, user.ID, user.Handle, user.Did, "", "", ""); err != nil {
		s.log.ErrorContext(ctx, "Failed to initialize data repository", "error", err, "did", d)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	// return
	// }

	// if req.Handle != user.Handle {
	// 	if exists, err := s.db.UserExists(ctx, "handle", req.Handle); err != nil {
	// 		s.log.ErrorContext(ctx, "Handle check failed", "error", err, "user", req.Email)
	// 		refErr.InternalServer().WriteResponse(w)
	// 		return
	// 	} else if exists {
	// 		fieldErr := refErr.FieldError{Field: auth.HANDLE, Message: "Handle already exists"}
	// 		fieldErr.Conflict().WriteResponse(w)
	// 		return
	// 	}
	// }
	//
	// s.log.InfoContext(ctx, "Reactivating soft deleted user", "user", req.Email)
	// updateUser := &common.User{
	// 	Name:           req.Name,
	// 	Handle:         req.Handle,
	// 	HashedPassword: hashedPassword,
	// 	Settings:       &common.UserSettings{Deleted: false},
	// }
	//
	// if err := s.db.UpdateWithTx(ctx, tx, updateUser, "id"); err != nil {
	// 	s.log.ErrorContext(ctx, "Failed to reactivate user", "error", err, "user", req.Email)
	// 	refErr.InternalServer().WriteResponse(w)
	// 	return
	// }
}

func (s *Server) handleLogin(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	if err := r.ParseForm(); err != nil {
		s.log.ErrorContext(ctx, "Invalid form", "error", err)
		refErr.BadRequest("Faild to parse form data from request").WriteResponse(w)
		return
	}

	login := auth.LoginRequest{
		GrantType: r.Form.Get(auth.GRANTTYPE),
		Email:     r.Form.Get(auth.EMAIL),
		Password:  r.Form.Get(auth.PASSWORD),
	}

	if err := login.Validate(ctx); err != nil {
		err.WriteResponse(w)
		return
	}

	defaultErr := refErr.FieldError{Field: auth.EMAIL, Message: "Email or password not found"}
	user, err := s.db.AuthenticateUser(ctx, login.Email)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to authenticate user", "error", err)
		if err == sql.ErrNoRows {
			defaultErr.NotFound().WriteResponse(w)
			return
		}
		refErr.InternalServer().WriteResponse(w)
		return
	}

	if ok, pwErr := common.VerifyPassword(login.Password, user.HashedPassword); pwErr != nil {
		s.log.ErrorContext(ctx, "Error verifying password", "error", pwErr)
		refErr.InternalServer().WriteResponse(w)
	} else if !ok {
		s.log.Error("Invalid login password")
		defaultErr.NotFound().WriteResponse(w)
	}

	s.log.Info(user.Did)

	accessToken, err := s.createToken(user.Did, Access)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to create access token", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}
	refreshToken, err := s.createToken(user.Did, Refresh)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to create refresh token", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	resp := auth.TokenResponse{
		UserID:       user.ID,
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    s.jwtConfig.AuthScheme,
	}
	encode(w, http.StatusOK, resp)
}

func (s *Server) handleRefresh(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Extract the refresh token from the request
	var req auth.RefreshRequest
	// req, err := decodeAndValidate[*auth.RefreshRequest](r)
	if err := s.decodeAndValidate(r, &req); err != nil {
		err.WriteResponse(w)
		return
	}

	// Parse and validate the token
	token, err := s.decodeJWT(req.RefreshToken)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to decode refresh token", "error", err)
		refErr.Unauthorized("Invalid refresh token").WriteResponse(w)
		return
	}

	email, err := s.validateToken(token, Refresh)
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

	accessToken, err := s.createToken(user.Did, Access)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to create access token", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}
	refreshToken, err := s.createToken(user.Did, Refresh)
	if err != nil {
		s.log.ErrorContext(ctx, "Failed to create refresh token", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	resp := auth.TokenResponse{
		UserID:       user.ID,
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    s.jwtConfig.AuthScheme,
	}
	encode(w, http.StatusOK, resp)
}
