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

func (v *View) ValidateHandle(ctx context.Context, handle string) *refErr.APIError {
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

// ResolveNewUser validates if the new account request can be handled and returns a hashed password
func (v *View) ResolveNewUser(ctx context.Context, req *refApp.ServerCreateAccount_Input) (string, *refErr.APIError) {
	filter := sq.Eq{"email": req.Email}
	if exists, err := v.meta.userExists(ctx, filter); err != nil {
		v.log.ErrorContext(ctx, "Error checking database for user email", "error", err)
		return "", refErr.InternalServer()
	} else if exists {
		nerr := errors.New("email already exists")
		v.log.ErrorContext(ctx, nerr.Error(), "email", req.Email)
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
	email string,
	hashedpassword string,
) *refErr.APIError {
	if err := v.meta.insertActorAndUserRecords(ctx, actor, email, hashedpassword); err != nil {
		return refErr.Database()
	}
	return nil
}

// GetAuthenticatedUser validates username (which can be email or handle) and password
func (v *View) GetAuthenticatedUser(
	ctx context.Context,
	username string,
	pw string,
) (*atp.User, *refErr.APIError) {
	// TODO - improve this flow by using caching

	defaultErr := refErr.FieldError{Message: "Username or password not found"}

	// First try to fetch the user by email
	user, err := v.meta.LookupUserByEmail(ctx, username)
	if err != nil && !errors.Is(err, sql.ErrNoRows) {
		v.log.ErrorContext(ctx, "Failed to fetch user details by email", "error", err, "username", username)
		return nil, defaultErr.NotFound()
	}

	// If user not found by email, try to fetch by handle through the Actor table
	if user == nil || errors.Is(err, sql.ErrNoRows) {
		user, err = v.meta.LookupUserByHandle(ctx, username)
		if err != nil {
			return nil, defaultErr.NotFound()
		}
	}

	// Verify the password
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

// DeleteActor deletes an actor record from the DB
func (v *View) DeleteActor(ctx context.Context, aid atp.Aid, did string) *refErr.APIError {
	if err := v.meta.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		nullHandle := sql.NullString{Valid: false}
		deletedAt := sql.NullTime{Time: time.Now(), Valid: true}
		actor := atp.Actor{
			Handle:    nullHandle,
			DeletedAt: deletedAt,
		}
		if err := v.meta.UpdateWithTx(ctx, tx, actor, sq.Eq{"id": aid}); err != nil {
			v.log.ErrorContext(ctx, "Failed to delete actor handle", "error", err)
			return err
		}
		return nil
	}); err != nil {
		return refErr.Database()
	}

	return nil
}

// DeleteUser deletes a user and user record from the DB
func (v *View) DeleteUser(ctx context.Context, aid atp.Aid, did string) *refErr.APIError {
	if err := v.meta.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		deletedAt := sql.NullTime{Time: time.Now(), Valid: true}

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

// DeleteLegislator deletes a user and user record from the DB
func (v *View) DeleteLegislator(ctx context.Context, aid atp.Aid, did string) *refErr.APIError {
	if err := v.meta.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		deletedAt := sql.NullTime{Time: time.Now(), Valid: true}

		legislator := atp.Legislator{Base: atp.Base{DeletedAt: deletedAt}}
		if err := v.meta.UpdateWithTx(ctx, tx, legislator, sq.Eq{"aid": aid}); err != nil {
			v.log.ErrorContext(ctx, "Failed to delete legislator", "error", err)
			return err
		}

		return nil
	}); err != nil {
		return refErr.Database()
	}

	return nil
}

// UpdateUserProfile updates a user profile with a new handle, email, or display name
func (v *View) UpdateUserProfile(
	ctx context.Context,
	aid atp.Aid,
	req *refApp.UserUpdateProfile_Input,
) *refErr.APIError {
	var newActor atp.Actor
	var newUser atp.User

	if req.Handle != nil {
		handle := *req.Handle
		if err := v.ValidateHandle(ctx, handle); err != nil {
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
		newActor.DisplayName = *req.DisplayName
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

// UpdateLegislator updates a legislator in the DB
func (v *View) UpdateLegislator(
	ctx context.Context,
	aid atp.Aid,
	req *refApp.LegislatorUpdateProfile_Input,
) *refErr.APIError {
	var newActor atp.Actor

	if req.Handle != nil {
		handle := *req.Handle
		if err := v.ValidateHandle(ctx, handle); err != nil {
			v.log.ErrorContext(ctx, "Error validating handle", "error", err)
			return err
		}
		newActor.Handle = sql.NullString{String: handle, Valid: true}
	}

	if req.Name != nil {
		newActor.DisplayName = *req.Name
	}

	if err := v.meta.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		if err := v.meta.UpdateWithTx(
			ctx, tx, &newActor, sq.Eq{"id": aid},
		); err != nil && !errors.Is(err, database.ErrNoFields) {
			v.log.ErrorContext(ctx, "Failed to update actor", "error", err)
			return err
		}

		return nil
	}); err != nil {
		return refErr.Database()
	}

	return nil
}
