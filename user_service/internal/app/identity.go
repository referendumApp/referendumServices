package app

import (
	"context"
	"database/sql"
	"errors"
	"strings"
	"time"

	sq "github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refApp "github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

func (v *View) validateHandle(ctx context.Context, handle string) *refErr.APIError {
	if !strings.HasSuffix(handle, v.handleSuffix) {
		fieldErr := refErr.FieldError{Field: "handle", Message: "Invalid handle format"}
		return fieldErr.Invalid()
	}

	filter := sq.Eq{"handle": handle}
	if exists, err := v.meta.actorExists(ctx, filter); err != nil {
		v.log.ErrorContext(ctx, "Error checking database for user handle", "error", err)
		return refErr.InternalServer()
	} else if exists {
		fieldErr := refErr.FieldError{Field: "handle", Message: "Handle already exists"}
		return fieldErr.Conflict()
	}

	return nil
}

// ResolveHandle validates handle, email, and password for create account request
func (v *View) ResolveHandle(ctx context.Context, req *refApp.ServerCreateAccount_Input) (string, *refErr.APIError) {
	if err := v.validateHandle(ctx, req.Handle); err != nil {
		v.log.ErrorContext(ctx, "Error validating handle", "error", err)
		return "", err
	}

	filter := sq.Eq{"email": req.Email}
	if exists, err := v.meta.userExists(ctx, filter); err != nil {
		v.log.ErrorContext(ctx, "Error checking database for user email", "error", err)
		return "", refErr.InternalServer()
	} else if exists {
		nerr := errors.New("email already exists")
		v.log.ErrorContext(ctx, nerr.Error(), "user", req.Email)
		fieldErr := refErr.FieldError{Field: "email", Message: nerr.Error()}
		return "", fieldErr.Conflict()
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

	hashedPassword, err := util.HashPassword(req.Password, util.DefaultParams())
	if err != nil {
		v.log.ErrorContext(ctx, "Failed to hash password", "error", err)
		return "", refErr.InternalServer()
	}

	return hashedPassword, nil
}

// SaveActorAndUser inserts a actor and user record to the DB
func (v *View) SaveActorAndUser(
	ctx context.Context,
	actor *atp.Actor,
	handle string,
	dname string,
) *refErr.APIError {
	if err := v.meta.insertActorAndUserRecords(ctx, actor, handle, dname); err != nil {
		return refErr.Database()
	}
	return nil
}

// GetAuthenticatedUser validates username and password for a create session request
func (v *View) GetAuthenticatedUser(ctx context.Context, username string, pw string) (*atp.User, *refErr.APIError) {
	defaultErr := refErr.FieldError{Message: "Email or password not found"}
	user, err := v.meta.getUserForEmail(ctx, username)
	if err != nil {
		v.log.ErrorContext(ctx, "Failed to fetch user details", "error", err, "username", username)
		if errors.Is(err, sql.ErrNoRows) {
			return nil, defaultErr.NotFound()
		}
		return nil, refErr.InternalServer()
	}

	if ok, verr := util.VerifyPassword(pw, user.HashedPassword.String); verr != nil {
		v.log.ErrorContext(ctx, "Error verifying password", "error", verr, "username", username)
		return nil, refErr.InternalServer()
	} else if !ok {
		v.log.ErrorContext(ctx, "Invalid login password", "username", username)
		return nil, defaultErr.NotFound()
	}

	return user, nil
}

// AuthenticateSession validates a session based on the user ID and DID
func (v *View) AuthenticateSession(ctx context.Context, aid atp.Aid, did string) *refErr.APIError {
	filter := sq.Eq{"id": aid, "did": did}
	exists, err := v.meta.actorExists(ctx, filter)
	if err != nil {
		v.log.ErrorContext(ctx, "Failed to lookup user", "error", err)
		return refErr.BadRequest("Failed to find user with refresh token")
	} else if !exists {
		v.log.ErrorContext(ctx, "User does not exist", "aid", aid, "did", did)
		return refErr.NotFound(aid, "user ID")
	}

	return nil
}

// DeleteAccount deletes a user and user record from the DB
func (v *View) DeleteAccount(ctx context.Context, aid atp.Aid, did string) *refErr.APIError {
	if err := v.meta.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		deletedAt := sql.NullTime{Time: time.Now(), Valid: true}

		if err := v.meta.UpdateWithTx(ctx, tx, atp.Actor{DeletedAt: deletedAt}, sq.Eq{"id": aid}); err != nil {
			v.log.ErrorContext(ctx, "Failed to delete user", "error", err)
			return err
		}

		user := atp.User{Base: atp.Base{DeletedAt: deletedAt}}
		if err := v.meta.UpdateWithTx(ctx, tx, user, sq.Eq{"aid": aid}); err != nil {
			v.log.ErrorContext(ctx, "Failed to delete user", "error", err)
			return err
		}

		return nil
	}); err != nil {
		return refErr.Database()
	}

	return nil
}

// UpdateProfile updates a user profile with a new handle, email, or display name
func (v *View) UpdateProfile(ctx context.Context, aid atp.Aid, req *refApp.UserUpdateProfile_Input) *refErr.APIError {
	var newActor atp.Actor
	var newUser atp.User

	if req.Handle != nil {
		handle := *req.Handle
		if err := v.validateHandle(ctx, handle); err != nil {
			v.log.ErrorContext(ctx, "Error validating handle", "error", err)
			return err
		}
		newActor.Handle = sql.NullString{String: handle, Valid: true}
	}

	if req.Email != nil {
		email := *req.Email
		exists, err := v.meta.userExists(ctx, sq.Eq{"email": email})
		if err != nil {
			v.log.ErrorContext(ctx, "Error checking database for user email", "error", err)
			return refErr.Database()
		} else if exists {
			v.log.ErrorContext(ctx, "Email already registered", "email", email)
			fieldErr := refErr.FieldError{Field: "email", Message: "Email already exists"}
			return fieldErr.Conflict()
		}
		newUser.Email = sql.NullString{String: email, Valid: true}
	}

	if req.DisplayName != nil {
		newUser.DisplayName = *req.DisplayName
	}

	if err := v.meta.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		if err := v.meta.UpdateWithTx(ctx, tx, &newActor, sq.Eq{"id": aid}); err != nil && !errors.Is(err, database.ErrNoFields) {
			v.log.ErrorContext(ctx, "Failed to update actor", "error", err)
			return err
		}

		if err := v.meta.UpdateWithTx(ctx, tx, &newUser, sq.Eq{"aid": aid}); err != nil && !errors.Is(err, database.ErrNoFields) {
			v.log.ErrorContext(ctx, "Failed to update user profile", "error", err)
			return err
		}

		return nil
	}); err != nil {
		return refErr.Database()
	}

	return nil
}
