package app

import (
	"context"
	"errors"

	sq "github.com/Masterminds/squirrel"
	"github.com/ipfs/go-cid"
	"github.com/jackc/pgx/v5"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

// HandleGraphFollow proccesses a follow request for another actor
func (v *View) HandleGraphFollow(
	ctx context.Context,
	aid atp.Aid,
	did string,
	cc cid.Cid,
	tid string,
) *refErr.APIError {
	target, err := v.meta.LookupUserByDid(ctx, did)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return refErr.NotFound(did, "DID")
		}

		return refErr.Database()
	}

	if err := v.meta.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		// TODO: Should be able to combine these queries with a CTE to speed things up
		if err := v.meta.CreateWithTx(ctx, tx, &atp.ActorFollowRecord{Rkey: tid, Cid: atp.DbCID{CID: cc}, Follower: aid, Target: target.Aid}); err != nil {
			return err
		}

		followerFilter := sq.Eq{"aid": aid}
		if err := v.meta.UpdateCountWithTx(ctx, tx, &atp.User{}, "following", followerFilter); err != nil {
			return err
		}

		targetFilter := sq.Eq{"id": target.ID}
		if err := v.meta.UpdateCountWithTx(ctx, tx, &atp.User{}, "followers", targetFilter); err != nil {
			return err
		}

		return nil
	}); err != nil {
		v.log.ErrorContext(ctx, "Failed to update actor follow record", "error", err)
		return refErr.Database()
	}

	return nil
}

// HandleGraphFollowers queries the actor_follow_record table for followering users
func (v *View) HandleGraphFollowers(ctx context.Context, aid atp.Aid) ([]*atp.UserBasic, *refErr.APIError) {
	followers, err := v.meta.LookupGraphFollowers(ctx, aid)
	if err != nil {
		return nil, refErr.Database()
	}

	return followers, nil
}

// HandleGraphFollowing queries the actor_follow_record table for followed users
func (v *View) HandleGraphFollowing(ctx context.Context, aid atp.Aid) ([]*atp.UserBasic, *refErr.APIError) {
	following, err := v.meta.LookupGraphFollowing(ctx, aid)
	if err != nil {
		return nil, refErr.Database()
	}

	return following, nil
}
