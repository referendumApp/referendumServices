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

// HandleGraphFollow proccesses a follow request for another user
func (v *View) HandleGraphFollow(
	ctx context.Context,
	uid atp.Aid,
	did string,
	cc cid.Cid,
	tid string,
) *refErr.APIError {
	target, err := v.meta.LookupPersonByDid(ctx, did)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return refErr.NotFound(did, "DID")
		}

		return refErr.Database()
	}

	if err := v.meta.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		// TODO: Should be able to combine these queries with a CTE to speed things up
		if err := v.meta.CreateWithTx(ctx, tx, &atp.UserFollowRecord{Rkey: tid, Cid: atp.DbCID{CID: cc}, Follower: uid, Target: target.Uid}); err != nil {
			return err
		}

		followerFilter := sq.Eq{"uid": uid}
		if err := v.meta.UpdateCountWithTx(ctx, tx, &atp.Person{}, "following", followerFilter); err != nil {
			return err
		}

		targetFilter := sq.Eq{"id": target.ID}
		if err := v.meta.UpdateCountWithTx(ctx, tx, &atp.Person{}, "followers", targetFilter); err != nil {
			return err
		}

		return nil
	}); err != nil {
		v.log.ErrorContext(ctx, "Failed to update user follow record", "error", err)
		return refErr.Database()
	}

	return nil
}

// HandleGraphFollowers queries the user_follow_record table for user followers
func (v *View) HandleGraphFollowers(ctx context.Context, uid atp.Aid) ([]*atp.PersonBasic, *refErr.APIError) {
	followers, err := v.meta.LookupGraphFollowers(ctx, uid)
	if err != nil {
		return nil, refErr.Database()
	}

	return followers, nil
}

// HandleGraphFollowing queries the user_follow_record table for user follows
func (v *View) HandleGraphFollowing(ctx context.Context, uid atp.Aid) ([]*atp.PersonBasic, *refErr.APIError) {
	following, err := v.meta.LookupGraphFollowing(ctx, uid)
	if err != nil {
		return nil, refErr.Database()
	}

	return following, nil
}
