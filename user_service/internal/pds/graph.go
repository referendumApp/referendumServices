package pds

import (
	"context"
	"net/http"
	"time"

	"github.com/jackc/pgx/v5"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
	"github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

func (p *PDS) HandleGraphFollow(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	per, ok := util.GetAndValidatePerson(w, ctx, p.log)
	if !ok {
		return
	}

	var req referendumapp.GraphFollow_Input
	if err := util.DecodeAndValidate(w, r, p.log, &req); err != nil {
		return
	}

	target, err := p.db.LookupPersonByDid(ctx, req.Did)
	if err != nil {
		if err == pgx.ErrNoRows {
			refErr.NotFound(req.Did, "DID").WriteResponse(w)
			return
		}

		refErr.Database().WriteResponse(w)
		return
	}

	rec := &referendumapp.GraphFollow{Subject: req.Did, CreatedAt: time.Now().UTC().Format(util.ISO8601)}
	cc, tid, err := p.repoman.CreateRecord(ctx, per.Uid, rec)
	if err != nil {
		p.log.Error("Error creating follow record", "error", err, "id", per.Uid)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	if err := p.db.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		// TODO: Should be able to combine these queries with a CTE to speed things up
		if err := p.db.CreateWithTx(ctx, tx, atp.UserFollowRecord{Rkey: tid, Cid: atp.DbCID{CID: cc}, Follower: per.Uid, Target: target.Uid}); err != nil {
			return err
		}

		if err := p.db.UpdateWithTx(ctx, tx, atp.Person{Base: atp.Base{ID: per.ID}, Following: per.Following + 1}, "id"); err != nil {
			return err
		}

		if err := p.db.UpdateWithTx(ctx, tx, atp.Person{Base: atp.Base{ID: target.ID}, Followers: target.Followers + 1}, "id"); err != nil {
			return err
		}

		return nil
	}); err != nil {
		refErr.Database().WriteResponse(w)
	}
}
