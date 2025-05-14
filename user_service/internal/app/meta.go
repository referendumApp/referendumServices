package app

import (
	"context"
	"database/sql"
	"fmt"

	sq "github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
)

// ViewMeta embeds the DB specifically for app view related queries
type ViewMeta struct {
	*database.DB
}

func (vm *ViewMeta) insertActorAndUserRecords(
	ctx context.Context,
	actor *atp.Actor,
	handle string,
	dname string,
) error {
	return vm.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		row, err := database.CreateReturningWithTx(ctx, vm.DB, tx, actor, "id")
		if err != nil {
			vm.Log.ErrorContext(ctx, "Failed to create actor", "error", err)
			return err
		}

		if serr := row.Scan(&actor.ID); serr != nil {
			vm.Log.ErrorContext(ctx, "Failed to scan new Actor ID", "error", serr)
			return serr
		}

		user := &atp.User{
			Aid:         actor.ID,
			Did:         actor.Did,
			Handle:      sql.NullString{String: handle, Valid: true},
			DisplayName: dname,
		}

		if err := vm.CreateWithTx(ctx, tx, user); err != nil {
			vm.Log.ErrorContext(ctx, "Failed to create user", "error", err)
			return err
		}

		// if handle != user.Handle {
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
		return nil
	})
}

func (vm *ViewMeta) authenticateActor(ctx context.Context, aname string) (*atp.Actor, error) {
	var actor atp.Actor
	sql := fmt.Sprintf(
		"SELECT id, email, hashed_password FROM %s.%s WHERE deleted_at IS NULL AND (email = $1 OR handle = $1)",
		vm.Schema,
		actor.TableName(),
	)

	if err := vm.GetRow(ctx, sql, aname).Scan(&actor.ID, &actor.Email, &actor.HashedPassword); err != nil {
		return nil, err
	}

	return &actor, nil
}

func (vm *ViewMeta) actorExists(ctx context.Context, filter sq.Eq) (bool, error) {
	var exists bool
	innerSql, args, err := sq.Select("id").
		From(vm.Schema + ".actor").
		Where(filter).
		PlaceholderFormat(sq.Dollar).ToSql()

	if err != nil {
		vm.Log.InfoContext(ctx, "Error building actor exists query", "error", err)
		return false, err
	}

	sql := fmt.Sprintf("SELECT EXISTS(%s)", innerSql)
	err = vm.DB.GetRow(ctx, sql, args...).Scan(&exists)

	return exists, err
}

func (vm *ViewMeta) lookupActorQuery(ctx context.Context, filter sq.Sqlizer) (*atp.Actor, error) {
	var entity atp.Actor
	actor, err := database.GetAll(ctx, vm.DB, entity, filter)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Failed to lookup actor", "filter", filter)
		return nil, err
	}

	return actor, nil
}

// LookupActorByID queries actor record by actor ID
func (vm *ViewMeta) LookupActorByID(ctx context.Context, aid atp.Aid) (*atp.Actor, error) {
	filter := sq.Eq{"id": aid}
	return vm.lookupActorQuery(ctx, filter)
}

// LookupActorByDid queries actor record by actor DID
func (vm *ViewMeta) LookupActorByDid(ctx context.Context, did string) (*atp.Actor, error) {
	filter := sq.Eq{"did": did}
	return vm.lookupActorQuery(ctx, filter)
}

// LookupActorByHandle queries actor record by actor handle
func (vm *ViewMeta) LookupActorByHandle(ctx context.Context, handle string) (*atp.Actor, error) {
	filter := sq.Eq{"handle": handle}
	return vm.lookupActorQuery(ctx, filter)
}

// LookupActorByEmail queries actor record by actor email
func (vm *ViewMeta) LookupActorByEmail(ctx context.Context, email string) (*atp.Actor, error) {
	filter := sq.Eq{"email": email}
	return vm.lookupActorQuery(ctx, filter)
}

// LookupGraphFollowers queries user records with a join to user_follow_record filtered by 'target'
func (vm *ViewMeta) LookupGraphFollowers(ctx context.Context, aid atp.Aid) ([]*atp.UserBasic, error) {
	filter := sq.Eq{"target": aid}
	var leftTbl atp.UserBasic
	var rightTbl atp.ActorFollowRecord

	followers, err := database.SelectLeft(ctx, vm.DB, leftTbl, "aid", rightTbl, "follower", filter)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Failed to lookup followers", "aid", aid)
		return nil, err
	}

	return followers, nil
}

// LookupGraphFollowing queries actor records with a join to actor_follow_record filtered by 'follower'
func (vm *ViewMeta) LookupGraphFollowing(ctx context.Context, aid atp.Aid) ([]*atp.UserBasic, error) {
	filter := sq.Eq{"follower": aid}
	var leftTbl atp.UserBasic
	var rightTbl atp.ActorFollowRecord

	following, err := database.SelectLeft(ctx, vm.DB, leftTbl, "aid", rightTbl, "target", filter)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Failed to lookup followers", "aid", aid)
		return nil, err
	}

	return following, nil
}

// GetUserBasicProfile queries user record for the basic profile
func (vm *ViewMeta) GetUserBasicProfile(ctx context.Context, aid atp.Aid) (*atp.UserBasic, error) {
	query, err := database.BuildSelect(&atp.UserBasic{}, vm.Schema, sq.Eq{"aid": aid})
	if err != nil {
		vm.Log.ErrorContext(ctx, "Error building profile select query", "error", err)
		return nil, err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		vm.Log.ErrorContext(ctx, "Error compiling profile select query", "error", err)
		return nil, err
	}

	profile, err := database.Get[atp.UserBasic](ctx, vm.DB, sql, args...)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Failed getting profile", "sql", sql, "aid", aid)
		return nil, err
	}

	return profile, nil
}
