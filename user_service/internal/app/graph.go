package app

import (
	"context"
	"database/sql"
	"time"

	sq "github.com/Masterminds/squirrel"
	"github.com/ipfs/go-cid"
	"github.com/jackc/pgx/v5"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

// HandleGraphFollow proccesses a follow request for another actor
func (v *View) HandleGraphFollow(
	ctx context.Context,
	aid atp.Aid,
	targetID atp.Aid,
	targetCollection string,
	cc cid.Cid,
	collection string,
	tid string,
) *refErr.APIError {
	if err := v.meta.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		// TODO: Should be able to combine these queries with a CTE to speed things up
		actorFollow := &atp.ActorFollow{
			TargetCollection: targetCollection,
			Collection:       collection,
			Rkey:             tid,
			Cid:              atp.DbCID{CID: cc},
			FollowerID:       aid,
			TargetID:         targetID,
			Metadata:         atp.Metadata{DeletedAt: sql.NullTime{Valid: false}},
		}
		if err := v.meta.CreateConflictWithTx(ctx, tx, actorFollow, []string{"rkey", "cid", "deleted_at"}); err != nil {
			return err
		}

		followerFilter := sq.Eq{"aid": aid}
		if err := v.meta.UpdateIncrementWithTx(ctx, tx, &atp.User{}, "following", followerFilter); err != nil {
			return err
		}

		targetFilter := sq.Eq{"id": targetID}
		if err := v.meta.UpdateIncrementWithTx(ctx, tx, &atp.PublicServant{}, "followers", targetFilter); err != nil {
			return err
		}

		return nil
	}); err != nil {
		v.log.ErrorContext(ctx, "Failed to update actor follow record", "error", err)
		return refErr.Database()
	}

	return nil
}

// HandleGraphUnfollow proccesses an unfollow request for another actor
func (v *View) HandleGraphUnfollow(
	ctx context.Context,
	aid atp.Aid,
	targetID atp.Aid,
) (string, string, *refErr.APIError) {
	var collection string
	var rkey string

	if err := v.meta.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		// TODO: Should be able to combine these queries with a CTE to speed things up
		actorFollow := &atp.ActorFollow{
			Metadata: atp.Metadata{DeletedAt: sql.NullTime{Time: time.Now(), Valid: true}},
		}

		updateFilter := sq.Eq{"follower_id": aid, "target_id": targetID}
		row, err := database.UpdateReturningWithTx(ctx, v.meta.DB, tx, actorFollow, updateFilter, "target_collection", "rkey")
		if err != nil {
			return err
		}

		if serr := row.Scan(&collection, &rkey); serr != nil {
			v.log.ErrorContext(ctx, "Failed to scan collection and record key", "error", serr)
			return serr
		}

		followerFilter := sq.Eq{"aid": aid}
		if err := v.meta.UpdateDecrementWithTx(ctx, tx, &atp.User{}, "following", followerFilter); err != nil {
			return err
		}

		targetFilter := sq.Eq{"id": targetID}
		if err := v.meta.UpdateDecrementWithTx(ctx, tx, &atp.PublicServant{}, "followers", targetFilter); err != nil {
			return err
		}

		return nil
	}); err != nil {
		v.log.ErrorContext(ctx, "Failed to update actor follow record", "error", err)
		return "", "", refErr.Database()
	}

	return collection, rkey, nil
}

// // HandleGraphFollowers queries the actor_follow_record table for followering users
// func (v *View) HandleGraphFollowers(ctx context.Context, aid atp.Aid) ([]*atp.ActorBasic, *refErr.APIError) {
// 	followers, err := v.meta.LookupGraphFollowers(ctx, aid)
// 	if err != nil {
// 		return nil, refErr.Database()
// 	}
//
// 	return followers, nil
// }
//
// // HandleGraphFollowing queries the actor_follow_record table for followed users
// func (v *View) HandleGraphFollowing(ctx context.Context, aid atp.Aid) ([]*atp.ActorBasic, *refErr.APIError) {
// 	following, err := v.meta.LookupGraphFollowing(ctx, aid)
// 	if err != nil {
// 		return nil, refErr.Database()
// 	}
//
// 	return following, nil
// }
