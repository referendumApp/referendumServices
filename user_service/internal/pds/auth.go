package pds

import (
	"context"
	"database/sql"
	"net/http"

	"github.com/jackc/pgx/v5"

	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	"github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

func (p *PDS) HandleSignUp(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var req referendumapp.ServerCreateAccount_Input
	if err := util.DecodeAndValidate(w, r, p.log, &req); err != nil {
		return
	}

	if err := p.validateHandle(ctx, req.Handle); err != nil {
		p.log.ErrorContext(ctx, "Error validating handle", "error", err)
		err.WriteResponse(w)
		return
	}

	if exists, err := p.db.UserExists(ctx, "email", req.Email); err != nil {
		p.log.ErrorContext(ctx, "Error checking database for user email", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	} else if exists {
		p.log.ErrorContext(ctx, "Email already registered", "user", req.Email)
		fieldErr := refErr.FieldError{Field: "email", Message: "Email already exists"}
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
	hashedPassword, err := util.HashPassword(req.Password, util.DefaultParams())
	if err != nil {
		p.log.ErrorContext(ctx, "Failed to hash password", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	// if user == nil {
	var recoveryKey string
	if req.RecoveryKey != nil {
		recoveryKey = *req.RecoveryKey
	}
	if recoveryKey == "" {
		recoveryKey = p.signingKey.Public().DID()
	}

	d, err := p.plc.CreateDID(ctx, p.signingKey, recoveryKey, req.Handle, p.serviceUrl)
	if err != nil {
		p.log.ErrorContext(ctx, "Failed to create DID", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	p.log.InfoContext(ctx, "Creating new user", "did", d, "handle", req.Handle)
	user := atp.User{
		Handle:         sql.NullString{String: req.Handle, Valid: true},
		Email:          sql.NullString{String: req.Email, Valid: true},
		HashedPassword: sql.NullString{String: hashedPassword, Valid: true},
		RecoveryKey:    recoveryKey,
		Did:            d,
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

	if terr := p.db.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		newUser, err := database.CreateReturningWithTx(ctx, p.db, tx, user, "id")
		if err != nil {
			p.log.ErrorContext(ctx, "Failed to create user", "error", err, "did", d)
			return err
		}

		actor := &atp.Person{
			Uid:         newUser.ID,
			Did:         user.Did,
			Handle:      sql.NullString{String: req.Handle, Valid: true},
			DisplayName: *req.DisplayName,
			Settings:    &atp.Settings{Deleted: false},
		}

		if err := p.db.CreateWithTx(ctx, tx, actor); err != nil {
			p.log.ErrorContext(ctx, "Failed to create citizen", "error", err, "did", d)
			return err
		}

		user.ID = newUser.ID

		return nil
	}); terr != nil {
		refErr.InternalServer().WriteResponse(w)
		return
	}

	// if err := s.repoman.InitNewActor(ctx, user.ID, user.Handle, user.Did, user.Handle, "", ""); err != nil {
	// 	s.log.ErrorContext(ctx, "Failed to initialize data repository", "error", err, "did", d)
	// 	refErr.InternalServer().WriteResponse(w)
	// 	return
	// }

	profile := &referendumapp.PersonProfile{
		DisplayName: req.DisplayName,
	}

	if err := p.repoman.InitNewRepo(ctx, user.ID, d, profile); err != nil {
		p.log.ErrorContext(ctx, "Failed write profile record to car store", "error", err, "did", d)
		refErr.InternalServer().WriteResponse(w)
		return
	}

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
