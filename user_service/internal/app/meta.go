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

func (vm *ViewMeta) createUserAndPerson(ctx context.Context, user *atp.User, handle string, dname string) error {
	return vm.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		row, err := database.CreateReturningWithTx(ctx, vm.DB, tx, user, "id")
		if err != nil {
			vm.Log.ErrorContext(ctx, "Failed to create user", "error", err)
			return err
		}

		if serr := row.Scan(&user.ID); serr != nil {
			vm.Log.ErrorContext(ctx, "Failed to scan new User ID", "error", serr)
			return serr
		}

		actor := &atp.Person{
			Uid:         user.ID,
			Did:         user.Did,
			Handle:      sql.NullString{String: handle, Valid: true},
			DisplayName: dname,
			Settings:    &atp.Settings{Deleted: false},
		}

		if err := vm.CreateWithTx(ctx, tx, actor); err != nil {
			vm.Log.ErrorContext(ctx, "Failed to create person", "error", err)
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

func (vm *ViewMeta) authenticateUser(ctx context.Context, uname string) (*atp.User, error) {
	var user atp.User
	sql := fmt.Sprintf(
		"SELECT id, did, handle, hashed_password FROM %s.%s WHERE deleted_at IS NULL AND (email = $1 OR handle = $1)",
		vm.Schema,
		user.TableName(),
	)

	if err := vm.GetRow(ctx, sql, uname).Scan(&user.ID, &user.Did, &user.Handle, &user.HashedPassword); err != nil {
		return nil, err
	}

	return &user, nil
}

func (vm *ViewMeta) userExists(ctx context.Context, filter sq.Eq) (bool, error) {
	var exists bool
	innerSql, args, err := sq.Select("id").
		From(vm.Schema + ".user").
		Where(filter).
		PlaceholderFormat(sq.Dollar).ToSql()

	if err != nil {
		vm.Log.InfoContext(ctx, "Error building user exists query", "error", err)
		return false, err
	}

	sql := fmt.Sprintf("SELECT EXISTS(%s)", innerSql)

	err = vm.DB.GetRow(ctx, sql, args...).Scan(&exists)
	return exists, err
}

func (vm *ViewMeta) lookupUserQuery(ctx context.Context, filter sq.Sqlizer) (*atp.User, error) {
	var entity atp.User
	user, err := database.GetAll(ctx, vm.DB, entity, filter)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Failed to lookup user", "filter", filter)
		return nil, err
	}

	return user, nil
}

// LookupUserByID queries user record by user ID
func (vm *ViewMeta) LookupUserByID(ctx context.Context, aid atp.Aid) (*atp.User, error) {
	filter := sq.Eq{"id": aid}
	return vm.lookupUserQuery(ctx, filter)
}

// LookupUserByDid queries user record by user DID
func (vm *ViewMeta) LookupUserByDid(ctx context.Context, did string) (*atp.User, error) {
	filter := sq.Eq{"did": did}
	return vm.lookupUserQuery(ctx, filter)
}

// LookupUserByHandle queries user record by user handle
func (vm *ViewMeta) LookupUserByHandle(ctx context.Context, handle string) (*atp.User, error) {
	filter := sq.Eq{"handle": handle}
	return vm.lookupUserQuery(ctx, filter)
}

// LookupUserByEmail queries user record by user email
func (vm *ViewMeta) LookupUserByEmail(ctx context.Context, email string) (*atp.User, error) {
	filter := sq.Eq{"email": email}
	return vm.lookupUserQuery(ctx, filter)
}

// LookupGraphFollowers queries user records with a join to user_follow_record filtered by 'target'
func (vm *ViewMeta) LookupGraphFollowers(ctx context.Context, aid atp.Aid) ([]*atp.PersonBasic, error) {
	filter := sq.Eq{"target": aid}
	var leftTbl atp.PersonBasic
	var rightTbl atp.UserFollowRecord

	followers, err := database.SelectLeft(ctx, vm.DB, leftTbl, "aid", rightTbl, "follower", filter)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Failed to lookup followers", "aid", aid)
		return nil, err
	}

	return followers, nil
}

// LookupGraphFollowing queries user records with a join to user_follow_record filtered by 'follower'
func (vm *ViewMeta) LookupGraphFollowing(ctx context.Context, aid atp.Aid) ([]*atp.PersonBasic, error) {
	filter := sq.Eq{"follower": aid}
	var leftTbl atp.PersonBasic
	var rightTbl atp.UserFollowRecord

	following, err := database.SelectLeft(ctx, vm.DB, leftTbl, "aid", rightTbl, "target", filter)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Failed to lookup followers", "aid", aid)
		return nil, err
	}

	return following, nil
}

// GetPersonBasicProfile queries person record for the basic profile
func (vm *ViewMeta) GetPersonBasicProfile(ctx context.Context, aid atp.Aid) (*atp.PersonBasic, error) {
	query, err := database.BuildSelect(&atp.PersonBasic{}, vm.Schema, sq.Eq{"aid": aid})
	if err != nil {
		vm.Log.ErrorContext(ctx, "Error building profile select query", "error", err)
		return nil, err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		vm.Log.ErrorContext(ctx, "Error compiling profile select query", "error", err)
		return nil, err
	}

	profile, err := database.Get[atp.PersonBasic](ctx, vm.DB, sql, args...)
	if err != nil {
		vm.Log.ErrorContext(ctx, "Failed getting profile", "sql", sql, "aid", aid)
		return nil, err
	}

	return profile, nil
}
