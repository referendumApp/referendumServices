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

	if strings.Contains(strings.TrimSuffix(handle, v.handleSuffix), ".") {
		fieldErr := refErr.FieldError{Field: "handle", Message: "Invalid character '.'"}
		return fieldErr.Invalid()
	}

	filter := sq.Eq{"handle": handle}
	if exists, err := v.meta.UserExists(ctx, filter); err != nil {
		v.log.ErrorContext(ctx, "Error checking database for user handle", "error", err)
		return refErr.InternalServer()
	} else if exists {
		fieldErr := refErr.FieldError{Field: "handle", Message: "Handle already exists"}
		return fieldErr.Conflict()
	}

	return nil
}

func (v *View) ResolveHandle(ctx context.Context, req *refApp.ServerCreateAccount_Input) (string, *refErr.APIError) {
	if err := v.validateHandle(ctx, req.Handle); err != nil {
		v.log.ErrorContext(ctx, "Error validating handle", "error", err)
		return "", err
	}

	filter := sq.Eq{"email": req.Email}
	if exists, err := v.meta.UserExists(ctx, filter); err != nil {
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

	// If the user doesn't exist then create them
	hashedPassword, err := util.HashPassword(req.Password, util.DefaultParams())
	if err != nil {
		v.log.ErrorContext(ctx, "Failed to hash password", "error", err)
		return "", refErr.InternalServer()
	}

	return hashedPassword, nil
}

func (v *View) CreateUserAndPerson(ctx context.Context, user *atp.User, handle string, dname string) *refErr.APIError {
	if err := v.meta.createUserAndPerson(ctx, user, handle, dname); err != nil {
		return refErr.Database()
	}
	return nil
}

func (v *View) AuthenticateUser(ctx context.Context, username string, pw string) (*atp.User, *refErr.APIError) {
	defaultErr := refErr.FieldError{Field: "email", Message: "Email or password not found"}
	user, err := v.meta.AuthenticateUser(ctx, username)
	if err != nil {
		v.log.ErrorContext(ctx, "Failed to authenticate user", "error", err)
		if err == sql.ErrNoRows {
			return nil, defaultErr.NotFound()
		}
		return nil, refErr.InternalServer()
	}

	if ok, verr := util.VerifyPassword(pw, user.HashedPassword.String); verr != nil {
		v.log.ErrorContext(ctx, "Error verifying password", "error", verr)
		return nil, refErr.InternalServer()
	} else if !ok {
		v.log.ErrorContext(ctx, "Invalid login password")
		return nil, defaultErr.NotFound()
	}

	return user, nil
}

func (v *View) AuthenticateSession(ctx context.Context, uid atp.Uid, did string) *refErr.APIError {
	filter := sq.Eq{"id": uid, "did": did}
	exists, err := v.meta.UserExists(ctx, filter)
	if err != nil {
		v.log.ErrorContext(ctx, "Failed to lookup user", "error", err)
		return refErr.BadRequest("Failed to find user with refresh token")
	} else if !exists {
		v.log.ErrorContext(ctx, "User does not exist", "uid", uid, "did", did)
		return refErr.NotFound(uid, "user ID")
	}

	return nil
}

func (v *View) DeleteAccount(ctx context.Context, uid atp.Uid, did string) *refErr.APIError {
	if err := v.meta.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		updatedUser := atp.User{DeletedAt: sql.NullTime{Time: time.Now(), Valid: true}}
		if err := v.meta.UpdateWithTx(ctx, tx, updatedUser, sq.Eq{"id": uid}); err != nil {
			v.log.ErrorContext(ctx, "Failed to delete user", "error", err)
			return err
		}

		person := atp.Person{Handle: sql.NullString{Valid: false}, Settings: &atp.Settings{Deleted: true}}
		if err := v.meta.UpdateWithTx(ctx, tx, person, sq.Eq{"uid": uid}); err != nil {
			v.log.ErrorContext(ctx, "Failed to delete person", "error", err)
			return err
		}

		return nil
	}); err != nil {
		return refErr.Database()
	}

	return nil
}

func (v *View) UpdateProfile(ctx context.Context, uid atp.Uid, req *refApp.PersonUpdateProfile_Input) *refErr.APIError {
	var newUser atp.User
	if req.Handle != nil {
		handle := *req.Handle
		if err := v.validateHandle(ctx, handle); err != nil {
			v.log.ErrorContext(ctx, "Error validating handle", "error", err)
			return err
		}
		newUser.Handle = sql.NullString{String: handle, Valid: true}
	}

	if req.Email != nil {
		email := *req.Email
		if exists, err := v.meta.UserExists(ctx, sq.Eq{"email": email}); err != nil {
			v.log.ErrorContext(ctx, "Error checking database for user email", "error", err)
			return refErr.Database()
		} else if exists {
			v.log.ErrorContext(ctx, "Email already registered", "user", email)
			fieldErr := refErr.FieldError{Field: "email", Message: "Email already exists"}
			return fieldErr.Conflict()
		}
		newUser.Email = sql.NullString{String: email, Valid: true}
	}

	if err := v.meta.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		if err := v.meta.UpdateWithTx(ctx, tx, &newUser, sq.Eq{"id": uid}); err != nil && err != database.ErrNoFields {
			v.log.ErrorContext(ctx, "Failed to update user", "error", err)
			return err
		}

		actor := &atp.Person{
			DisplayName: *req.DisplayName,
			Handle:      newUser.Handle,
		}

		if err := v.meta.UpdateWithTx(ctx, tx, actor, sq.Eq{"uid": uid}); err != nil && err != database.ErrNoFields {
			v.log.ErrorContext(ctx, "Failed to update person profile", "error", err)
			return err
		}

		return nil
	}); err != nil {
		return refErr.Database()
	}

	return nil
}
