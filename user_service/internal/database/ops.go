package database

import (
	"context"
	"errors"
	"fmt"

	sq "github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
)

func (d *DB) lookupPDSQuery(ctx context.Context, filter sq.Sqlizer) (*atp.PDS, error) {
	var entity atp.PDS
	pds, err := GetAll(ctx, d, entity, filter)
	if err != nil {
		d.Log.ErrorContext(ctx, "Failed to lookup repost record", "filter", filter)
		return nil, err
	}

	return pds, nil
}

// LookupPDSById returns a PDS record by ID
func (d *DB) LookupPDSById(ctx context.Context, id int64) (*atp.PDS, error) {
	filter := sq.Eq{"id": id}
	return d.lookupPDSQuery(ctx, filter)
}

// LookupDidByAid returns a DID based on an actor ID
func (d *DB) LookupDidByAid(ctx context.Context, aid atp.Aid) (string, error) {
	var person atp.Person
	sql := fmt.Sprintf("SELECT did FROM %s.%s WHERE uid = $1", d.Schema, person.TableName())

	if err := d.pool.QueryRow(ctx, sql, aid).Scan(&person.Did); err != nil {
		d.Log.ErrorContext(ctx, "Failed to get DID for person", "aid", aid)
		return "", err
	}

	return person.Did, nil
}

func (d *DB) lookupPersonQuery(ctx context.Context, filter sq.Sqlizer) (*atp.Person, error) {
	var entity atp.Person
	person, err := GetAll(ctx, d, entity, filter)
	if err != nil {
		d.Log.ErrorContext(ctx, "Failed to lookup person", "filter", filter)
		return nil, err
	}

	return person, nil
}

// LookupPersonByAid returns a person record by actor ID
func (d *DB) LookupPersonByAid(ctx context.Context, aid atp.Aid) (*atp.Person, error) {
	filter := sq.Eq{"aid": aid}
	return d.lookupPersonQuery(ctx, filter)
}

// LookupPersonByDid returns a person record by DID
func (d *DB) LookupPersonByDid(ctx context.Context, did string) (*atp.Person, error) {
	filter := sq.Eq{"did": did}
	return d.lookupPersonQuery(ctx, filter)
}

// LookupPersonByHandle returns a person record by handle
func (d *DB) LookupPersonByHandle(ctx context.Context, handle string) (*atp.Person, error) {
	filter := sq.Eq{"handle": handle}
	return d.lookupPersonQuery(ctx, filter)
}

func (d *DB) lookupActivityPostQuery(ctx context.Context, filter ...sq.Sqlizer) (*atp.ActivityPost, error) {
	var entity atp.ActivityPost
	post, err := GetAll(ctx, d, entity, filter...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Failed to lookup feed post", "filter", filter)
		return nil, err
	}

	return post, nil
}

// LookupActivityPostByUid returns a activity_post record by actor ID
func (d *DB) LookupActivityPostByUid(ctx context.Context, rkey string, aid atp.Aid) (*atp.ActivityPost, error) {
	// Create the subquery for author ID
	filters := sq.Eq{"rkey": rkey, "author": aid}
	return d.lookupActivityPostQuery(ctx, filters)
}

// LookupActivityPostByDid returns a activity_post record by DID
func (d *DB) LookupActivityPostByDid(ctx context.Context, rkey string, did string) (*atp.ActivityPost, error) {
	// Create the subquery for author ID
	authorSubquery := sq.Select("id").
		From(atp.Person{}.TableName()).
		Where(sq.Eq{"did": did}).
		PlaceholderFormat(sq.Dollar)

	filters := sq.And{sq.Eq{"rkey": rkey}, sq.Expr("author = (?)", authorSubquery)}
	return d.lookupActivityPostQuery(ctx, filters)
}

// UpdateActivityPostUpCount increments the up_count column
func (d *DB) UpdateActivityPostUpCount(ctx context.Context, postId uint) error {
	return d.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		feedTbl := atp.ActivityPost{}.TableName()
		sql, args, err := sq.Update(feedTbl).
			Set("up_count", sq.Expr("up_count + 1")).
			Where(sq.Eq{"id": postId}).
			PlaceholderFormat(sq.Dollar).
			ToSql()
		if err != nil {
			d.Log.ErrorContext(ctx, "Error building update query", "error", err, "table", feedTbl)
			return err
		}

		if _, err := tx.Exec(ctx, sql, args...); err != nil {
			d.Log.ErrorContext(ctx, "Error executing statement", "error", err, "sql", sql)
			return err
		}

		return nil
	})
}

func (d *DB) lookupEndorsementRecordQuery(ctx context.Context, filter sq.Sqlizer) (*atp.EndorsementRecord, error) {
	var entity atp.EndorsementRecord
	vote, err := GetAll(ctx, d, entity, filter)
	if err != nil {
		d.Log.ErrorContext(ctx, "Failed to lookup repost record", "filter", filter)
		return nil, err
	}

	return vote, nil
}

// LookupEndorsementRecordByUid returns endorsement_record by actor ID
func (d *DB) LookupEndorsementRecordByUid(
	ctx context.Context,
	voter atp.Aid,
	rkey string,
) (*atp.EndorsementRecord, error) {
	filter := sq.Eq{"voter": voter}
	return d.lookupEndorsementRecordQuery(ctx, filter)
}

// HandleRecordDeleteFeedLike delete feed like
func (d *DB) HandleRecordDeleteFeedLike(ctx context.Context, uid atp.Aid, rkey string) error {
	var entity atp.EndorsementRecord
	filter := sq.Eq{"voter": uid, "rkey": rkey}
	er, err := GetAll(ctx, d, entity, filter)
	if err != nil {
		return err
	}

	return d.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		delFilter := sq.Eq{"id": er.ID}
		if err := d.DeleteWithTx(ctx, tx, er, delFilter); err != nil {
			return err
		}

		d.Log.Warn("need to delete vote notification")
		return nil
	})
}

// HandleRecordDeleteGraphFollow delete actor follow
func (d *DB) HandleRecordDeleteGraphFollow(ctx context.Context, uid atp.Aid, rkey string) error {
	filter := sq.Eq{"follower": uid, "rkey": rkey}
	if err := d.Delete(ctx, atp.ActorFollowRecord{}, filter); err != nil {
		if errors.Is(err, ErrNoRowsAffected) {
			d.Log.WarnContext(
				ctx,
				"Attempted to delete follow we did not have a record for",
				"actor",
				uid,
				"rkey",
				rkey,
			)
			return nil
		}
		return err
	}

	return nil
}
