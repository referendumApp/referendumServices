package database

import (
	"context"
	"fmt"

	sq "github.com/Masterminds/squirrel"
	"github.com/bluesky-social/indigo/models"
	"github.com/jackc/pgx/v5"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
	repo "github.com/referendumApp/referendumServices/internal/repository"
)

func (d *Database) lookupPDSQuery(ctx context.Context, filter repo.Filter) (*atp.PDS, error) {
	var entity atp.PDS
	pds, err := GetAll(ctx, d, entity, filter)
	if err != nil {
		d.log.ErrorContext(ctx, "Failed to lookup repost record", "filter", filter)
		return nil, err
	}

	return pds, nil
}

func (d *Database) LookupPDSById(ctx context.Context, id uint) (*atp.PDS, error) {
	filter := repo.Filter{Column: "id", Op: repo.Eq, Value: id}
	return d.lookupPDSQuery(ctx, filter)
}

func (d *Database) DidForActor(ctx context.Context, uid models.Uid) (string, error) {
	var actor atp.Citizen
	sql := fmt.Sprintf("SELECT did FROM %s WHERE uid = $1", actor.TableName())

	if err := d.pool.QueryRow(ctx, sql, uid).Scan(&actor.Did); err != nil {
		d.log.ErrorContext(ctx, "Failed to get DID for actor", "uid", uid)
		return "", err
	}

	return actor.Did, nil
}

func (d *Database) lookupActorQuery(ctx context.Context, filter repo.Filter) (*atp.Citizen, error) {
	var entity atp.Citizen
	actor, err := GetAll(ctx, d, entity, filter)
	if err != nil {
		d.log.ErrorContext(ctx, "Failed to lookup actor", "filter", filter)
		return nil, err
	}

	return actor, nil
}

func (d *Database) LookupActorByUid(ctx context.Context, uid models.Uid) (*atp.Citizen, error) {
	filter := repo.Filter{Column: "uid", Op: repo.Eq, Value: uid}
	return d.lookupActorQuery(ctx, filter)
}

func (d *Database) LookupActorByDid(ctx context.Context, did string) (*atp.Citizen, error) {
	filter := repo.Filter{Column: "did", Op: repo.Eq, Value: did}
	return d.lookupActorQuery(ctx, filter)
}

func (d *Database) LookupActorByHandle(ctx context.Context, handle string) (*atp.Citizen, error) {
	filter := repo.Filter{Column: "handle", Op: repo.Eq, Value: handle}
	return d.lookupActorQuery(ctx, filter)
}

func (d *Database) lookupActivityPostQuery(ctx context.Context, filter ...repo.Filter) (*atp.ActivityPost, error) {
	var entity atp.ActivityPost
	post, err := GetAll(ctx, d, entity, filter...)
	if err != nil {
		d.log.ErrorContext(ctx, "Failed to lookup feed post", "filter", filter)
		return nil, err
	}

	return post, nil
}

func (d *Database) LookupActivityPostByUid(ctx context.Context, rkey string, uid models.Uid) (*atp.ActivityPost, error) {
	// Create the subquery for author ID
	filters := []repo.Filter{{Column: "rkey", Op: repo.Eq, Value: rkey}, {Column: "author", Op: repo.Expr, Value: uid}}
	return d.lookupActivityPostQuery(ctx, filters...)
}

func (d *Database) LookupActivityPostByDid(ctx context.Context, rkey string, did string) (*atp.ActivityPost, error) {
	// Create the subquery for author ID
	authorSubquery := sq.Select("id").
		From(atp.Citizen{}.TableName()).
		Where(sq.Eq{"did": did}).
		PlaceholderFormat(sq.Dollar)

	filters := []repo.Filter{{Column: "rkey", Op: repo.Eq, Value: rkey}, {Column: "author", Op: repo.Expr, Value: authorSubquery}}
	return d.lookupActivityPostQuery(ctx, filters...)
}

func (d *Database) UpdateActivityPostUpCount(ctx context.Context, postId uint) error {
	return d.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		feedTbl := atp.ActivityPost{}.TableName()
		sql, args, err := sq.Update(feedTbl).
			Set("up_count", sq.Expr("up_count + 1")).
			Where(sq.Eq{"id": postId}).
			PlaceholderFormat(sq.Dollar).
			ToSql()
		if err != nil {
			d.log.ErrorContext(ctx, "Error building update query", "error", err, "table", feedTbl)
			return err
		}

		if _, err := d.PrepareAndExecute(ctx, tx, "update_activity_post", sql, args); err != nil {
			return err
		}

		return nil
	})
}

func (d *Database) lookupEndorsementRecordQuery(ctx context.Context, filter repo.Filter) (*atp.EndorsementRecord, error) {
	var entity atp.EndorsementRecord
	vote, err := GetAll(ctx, d, entity, filter)
	if err != nil {
		d.log.ErrorContext(ctx, "Failed to lookup repost record", "filter", filter)
		return nil, err
	}

	return vote, nil
}

func (d *Database) LookupEndorsementRecordByUid(ctx context.Context, voter models.Uid, rkey string) (*atp.EndorsementRecord, error) {
	filter := repo.Filter{Column: "voter", Op: repo.Eq, Value: voter}
	return d.lookupEndorsementRecordQuery(ctx, filter)
}

func (d *Database) HandleRecordDeleteFeedLike(ctx context.Context, uid models.Uid, rkey string) error {
	var entity atp.EndorsementRecord
	vrFilters := []repo.Filter{{Column: "voter", Op: repo.Eq, Value: uid}, {Column: "rkey", Op: repo.Eq, Value: rkey}}
	er, err := GetAll(ctx, d, entity, vrFilters...)
	if err != nil {
		return err
	}

	return d.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		delFilters := repo.Filter{Column: "id", Op: repo.Eq, Value: er.ID}

		delSql, delArgs, err := repo.BuildDeleteQuery(er, d.schema, delFilters)
		if err != nil {
			d.log.ErrorContext(ctx, "Error building delete query", "error", err, "table", er.TableName())
			return err
		}

		delTag, err := d.PrepareAndExecute(ctx, tx, "delete_endorsement_record", delSql, delArgs)
		if err != nil {
			return err
		}
		if delTag.RowsAffected() == 0 {
			return ErrNoRowsAffected
		}

		sql, args, err := repo.BuildUpdateQuery(er, d.schema, "id")
		if err != nil {
			d.log.ErrorContext(ctx, "Error building delete query", "error", err, "table", er.TableName())
			return err
		}

		tag, err := d.PrepareAndExecute(ctx, tx, "update_activity_post", sql, args)
		if err != nil {
			return err
		}
		if tag.RowsAffected() == 0 {
			return ErrNoRowsAffected
		}

		d.log.Warn("need to delete vote notification")
		return nil
	})
}

func (d *Database) HandleRecordDeleteGraphFollow(ctx context.Context, uid models.Uid, rkey string) error {
	filters := []repo.Filter{{Column: "follower", Op: repo.Eq, Value: uid}, {Column: "rkey", Op: repo.Eq, Value: rkey}}
	if err := d.Delete(ctx, atp.UserFollowRecord{}, filters...); err != nil {
		if err == ErrNoRowsAffected {
			d.log.Warn("Attempted to delete follow we did not have a record for", "user", uid, "rkey", rkey)
			return nil
		}
		return err
	}

	return nil
}
