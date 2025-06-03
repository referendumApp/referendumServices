package app

import (
	"context"
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

func (vm *ViewMeta) insertActorAndUserRecords(ctx context.Context, actor *atp.Actor, dname string) error {
	err := vm.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		row, err := database.CreateReturningWithTx(ctx, vm.DB, tx, actor, "id")
		if err != nil {
			vm.Log.ErrorContext(ctx, "Failed to create actor", "error", err)
			return err
		}
		if serr := row.Scan(&actor.ID); serr != nil {
			vm.Log.ErrorContext(ctx, "Failed to scan new Actor ID", "error", serr)
			return serr
		}

		if err := vm.CreateWithTx(ctx, tx, &atp.User{Did: actor.Did, Aid: actor.ID, DisplayName: dname}); err != nil {
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

	return err
}

func (vm *ViewMeta) insertActorAndLegislatorRecords(
	ctx context.Context,
	actor *atp.Actor,
	legislatorId int64,
	name string,
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

		legislator := &atp.Legislator{
			Aid:          actor.ID,
			LegislatorId: legislatorId,
			DisplayName:  name,
		}

		if err := vm.CreateWithTx(ctx, tx, legislator); err != nil {
			vm.Log.ErrorContext(ctx, "Failed to create legislator", "error", err)
			return err
		}

		return nil
	})
}

func (vm *ViewMeta) recordExists(ctx context.Context, entity database.TableEntity, filter sq.Eq) (bool, error) {
	var exists bool
	innerSql, args, err := sq.Select("1").
		From(vm.Schema + "." + entity.TableName()).
		Where(filter).
		PlaceholderFormat(sq.Dollar).ToSql()

	if err != nil {
		vm.Log.InfoContext(ctx, "Error building exists query", "error", err, "table", entity.TableName())
		return false, err
	}

	sql := fmt.Sprintf("SELECT EXISTS(%s)", innerSql)
	err = vm.DB.GetRow(ctx, sql, args...).Scan(&exists)

	return exists, err
}

func (vm *ViewMeta) lookupUserQuery(ctx context.Context, filter sq.Sqlizer) (*atp.User, error) {
	combinedFilter := sq.And{
		filter,
		sq.Eq{"deleted_at": nil},
	}

	var entity atp.User
	user, err := database.GetAll(ctx, vm.DB, entity, combinedFilter)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Failed to lookup user", "filter", combinedFilter)
		return nil, err
	}

	return user, nil
}

func (vm *ViewMeta) LookupUserByEmail(ctx context.Context, email string) (*atp.User, error) {
	actor, err := vm.LookupActorByEmail(ctx, email)
	if err != nil {
		return nil, err
	}
	return vm.LookupUserByAid(ctx, actor.ID)
}

func (vm *ViewMeta) LookupUserByHandle(ctx context.Context, handle string) (*atp.User, error) {
	actor, err := vm.LookupActorByHandle(ctx, handle)
	if err != nil {
		return nil, err
	}

	return vm.LookupUserByAid(ctx, actor.ID)
}

func (vm *ViewMeta) LookupUserByAid(ctx context.Context, aid atp.Aid) (*atp.User, error) {
	filter := sq.Eq{"aid": aid}
	return vm.lookupUserQuery(ctx, filter)
}

func (vm *ViewMeta) lookupLegislatorQuery(ctx context.Context, filter sq.Sqlizer) (*atp.Legislator, error) {
	combinedFilter := sq.And{
		filter,
		sq.Eq{"deleted_at": nil},
	}

	var entity atp.Legislator
	legislator, err := database.GetAll(ctx, vm.DB, entity, combinedFilter)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Failed to lookup legislator", "filter", combinedFilter)
		return nil, err
	}

	return legislator, nil
}

// LookupLegislatorByID queries actor record by actor ID
func (vm *ViewMeta) LookupLegislatorByID(ctx context.Context, id int64) (*atp.Legislator, error) {
	filter := sq.Eq{"legislator_id": id}
	return vm.lookupLegislatorQuery(ctx, filter)
}

// LookupLegislatorByDid queries actor record by actor DID
func (vm *ViewMeta) LookupLegislatorByDid(ctx context.Context, did string) (*atp.Legislator, error) {
	filter := sq.Eq{"did": did}
	return vm.lookupLegislatorQuery(ctx, filter)
}

// LookupLegislatorByHandle queries actor record by actor handle
func (vm *ViewMeta) LookupLegislatorByHandle(ctx context.Context, handle string) (*atp.Legislator, error) {
	actor, err := vm.LookupActorByHandle(ctx, handle)
	if err != nil {
		return nil, err
	}

	return vm.LookupLegislatorByAid(ctx, actor.ID)
}

// LookupLegislatorByAid queries actor record by actor handle
func (vm *ViewMeta) LookupLegislatorByAid(ctx context.Context, aid atp.Aid) (*atp.Legislator, error) {
	filter := sq.Eq{"aid": aid}
	return vm.lookupLegislatorQuery(ctx, filter)
}

func (vm *ViewMeta) getActorProfile(
	ctx context.Context,
	filter sq.Sqlizer,
) (*actorProfile, error) {
	combinedFilter := sq.And{sq.Eq{atp.Actor{}.TableName() + ".deleted_at": nil}, filter}

	profile, err := database.GetLeft(ctx, vm.DB, actorProfile{}, combinedFilter)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Error getting actor profile", "error", err)
		return nil, err
	}

	return profile, nil
}

// GetActorProfileByID queries actor table for profile data
func (vm *ViewMeta) GetActorProfileByID(ctx context.Context, aid atp.Aid) (*actorProfile, error) {
	filter := sq.Eq{atp.Actor{}.TableName() + ".id": aid}

	return vm.getActorProfile(ctx, filter)
}

func (vm *ViewMeta) authenticateActor(
	ctx context.Context,
	aname string,
) (*actorAuth, error) {
	filter := sq.And{
		sq.Eq{atp.Actor{}.TableName() + ".deleted_at": nil},
		sq.Or{
			sq.Eq{"email": aname},
			sq.Eq{"handle": aname},
		},
	}

	actor, err := database.GetLeft(ctx, vm.DB, actorAuth{}, filter)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Error querying actor profile and auth_settings", "error", err)
		return nil, err
	}

	return actor, nil
}

func (vm *ViewMeta) lookupActorQuery(ctx context.Context, filter sq.Sqlizer) (*atp.Actor, error) {
	combinedFilter := sq.And{
		filter,
		sq.Eq{"deleted_at": nil},
	}

	var entity atp.Actor
	actor, err := database.GetAll(ctx, vm.DB, entity, combinedFilter)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Failed to lookup actor", "filter", combinedFilter)
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

// LookupActorByEmail queries actor `record by actor email
func (vm *ViewMeta) LookupActorByEmail(ctx context.Context, email string) (*atp.Actor, error) {
	filter := sq.Eq{"email": email}
	return vm.lookupActorQuery(ctx, filter)
}

// GetAllPublicServantIDs queries to get all the aids and dids in the `public_servants` table
func (vm *ViewMeta) GetAllPublicServantIDs(ctx context.Context) ([]*publicServantIDs, error) {
	query, err := database.BuildSelect(&publicServantIDs{}, vm.Schema)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Failed to get public servant Aids and DIDs", "error", err)
		return nil, err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		vm.Log.ErrorContext(ctx, "Error building select query for public servant IDs", "error", err)
		return nil, err
	}

	ps, err := database.Select[publicServantIDs](ctx, vm.DB, sql, args...)
	if err != nil {
		return nil, err
	}

	return ps, nil
}

// // LookupGraphFollowers queries user records with a join to user_follow_record filtered by 'target'
// func (vm *ViewMeta) LookupGraphFollowers(ctx context.Context, aid atp.Aid) ([]*atp.ActorBasic, error) {
// 	filter := sq.Eq{"target": aid}
// 	var leftTbl atp.ActorBasic
// 	var rightTbl atp.ActorFollow
//
// 	followers, err := database.SelectLeft(ctx, vm.DB, leftTbl, "id", rightTbl, "follower", filter)
// 	if err != nil {
// 		vm.Log.ErrorContext(ctx, "Failed to lookup followers", "id", aid)
// 		return nil, err
// 	}
//
// 	return followers, nil
// }
//
// // LookupGraphFollowing queries actor records with a join to actor_follow_record filtered by 'follower'
// func (vm *ViewMeta) LookupGraphFollowing(ctx context.Context, aid atp.Aid) ([]*atp.ActorBasic, error) {
// 	filter := sq.Eq{"follower": aid}
// 	var leftTbl atp.ActorBasic
// 	var rightTbl atp.ActorFollow
//
// 	following, err := database.SelectLeft(ctx, vm.DB, leftTbl, "id", rightTbl, "target", filter)
// 	if err != nil {
// 		vm.Log.ErrorContext(ctx, "Failed to lookup followers", "id", aid)
// 		return nil, err
// 	}
//
// 	return following, nil
// }
