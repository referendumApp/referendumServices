package pds

import (
	"context"
	"database/sql"
	"fmt"
	"net/http"
	"time"

	"github.com/jackc/pgx/v5"

	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	"github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/plc"
	"github.com/referendumApp/referendumServices/internal/util"
)

func findLatestOp(log *[]plc.Op) (*plc.Op, error) {
	derefLog := *log

	if len(derefLog) == 0 {
		return nil, fmt.Errorf("no operations found in PLC log")
	}

	newest := &derefLog[0]

	for _, op := range derefLog[1:] {
		if op.CreatedAt.After(newest.CreatedAt) {
			newest = &op
		}
	}

	return newest, nil
}

func (p *PDS) HandleUserDelete(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	per, ok := util.GetAndValidatePerson(w, ctx, p.log)
	if !ok {
		return
	}

	if err := p.db.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		updatedUser := atp.User{ID: per.Uid, DeletedAt: sql.NullTime{Time: time.Now(), Valid: true}}
		if err := p.db.UpdateWithTx(ctx, tx, updatedUser, "id"); err != nil {
			return fmt.Errorf("failed to delete user")
		}

		person := atp.Person{Uid: per.Uid, Handle: sql.NullString{Valid: false}, Settings: &atp.Settings{Deleted: true}}
		if err := p.db.UpdateWithTx(ctx, tx, person, "uid"); err != nil {
			return fmt.Errorf("failed to delete person")
		}

		return nil
	}); err != nil {
		refErr.InternalServer().WriteResponse(w)
		return
	}

	log, err := p.plc.GetOpAuditLog(ctx, per.Did)
	if err != nil {
		p.log.ErrorContext(ctx, "Request to PLC directory failed", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	op, err := findLatestOp(log)
	if err != nil {
		p.log.ErrorContext(ctx, "Error searching for latest operation in PLC log", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	if err := p.plc.TombstoneDID(ctx, p.signingKey, per.Did, op.CID); err != nil {
		p.log.ErrorContext(ctx, "Tombstone request to plc directory failed", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	if err := p.repoman.TakeDownRepo(ctx, per.Uid); err != nil {
		p.log.ErrorContext(ctx, "Failed to delete CAR shards", "error", err)
		return
	}

	if err := p.events.TakeDownRepo(ctx, per.Uid); err != nil {
		p.log.ErrorContext(ctx, "Failed to broadcast tombstone operation", "error", err)
		return
	}
}

func (p *PDS) HandleProfileUpdate(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	per, ok := util.GetAndValidatePerson(w, ctx, p.log)
	if !ok {
		return
	}

	var req referendumapp.PersonUpdateProfile_Input
	if err := util.DecodeAndValidate(w, r, p.log, &req); err != nil {
		return
	}

	var newUser atp.User
	if req.Handle != nil {
		if err := p.validateHandle(ctx, *req.Handle); err != nil {
			p.log.ErrorContext(ctx, "Error validating handle", "error", err)
			err.WriteResponse(w)
			return
		}
		newUser.Handle = sql.NullString{String: *req.Handle, Valid: true}
	}

	if req.Email != nil {
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
		newUser.Email = sql.NullString{String: *req.Email, Valid: true}
	}

	if err := p.db.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		if err := p.db.UpdateWithTx(ctx, tx, per, "id"); err != nil && err != database.ErrNoMappedFields {
			p.log.ErrorContext(ctx, "Failed to update user", "error", err, "did", per.Did)
			return err
		}

		actor := &atp.Person{
			Uid:         per.Uid,
			DisplayName: *req.DisplayName,
			Handle:      newUser.Handle,
		}

		if err := p.db.UpdateWithTx(ctx, tx, actor, "uid"); err != nil {
			p.log.ErrorContext(ctx, "Failed to update person profile", "error", err, "did", per.Did)
			return err
		}

		if req.DisplayName != nil {
			profile := &referendumapp.PersonProfile{
				DisplayName: req.DisplayName,
			}

			if _, err := p.repoman.UpdateRecord(ctx, per.Uid, profile); err != nil {
				p.log.Error("Error updating repo record", "error", err, "id", per.Uid)
				refErr.InternalServer().WriteResponse(w)
				return err
			}
		}

		return nil
	}); err != nil {
		refErr.InternalServer().WriteResponse(w)
		return
	}
}
