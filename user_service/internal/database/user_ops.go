package database

import (
	"context"
	"fmt"

	"github.com/bluesky-social/indigo/models"

	"github.com/referendumApp/referendumServices/internal/domain/common"
	repo "github.com/referendumApp/referendumServices/internal/repository"
)

func (d *Database) UserExists(ctx context.Context, field string, value any) (bool, error) {
	var exists bool
	sql := fmt.Sprintf("SELECT EXISTS(SELECT id FROM %s.user WHERE %s = $1)", d.schema, field)
	err := d.pool.QueryRow(ctx, sql, value).Scan(&exists)
	return exists, err
}

func (d *Database) AuthenticateUser(ctx context.Context, email string) (*common.User, error) {
	var user common.User
	sql := fmt.Sprintf("SELECT id, did, hashed_password FROM %s.%s WHERE email = $1", d.schema, user.TableName())

	if err := d.pool.QueryRow(ctx, sql, email).Scan(&user.ID, &user.Did, &user.HashedPassword); err != nil {
		return nil, err
	}

	return &user, nil
}

func (d *Database) AuthenticateHandle(ctx context.Context, user *common.User) (bool, error) {
	var exists bool
	sql := fmt.Sprintf("SELECT EXISTS(SELECT id FROM %s.%s WHERE email != $1 AND handle = $2)", d.schema, user.TableName())
	err := d.pool.QueryRow(ctx, sql, user.Email, user.Handle).Scan(&exists)

	return exists, err
}

func (d *Database) lookupUserQuery(ctx context.Context, filter repo.Filter) (*common.User, error) {
	var entity common.User
	actor, err := GetAll(ctx, d, entity, filter)
	if err != nil {
		d.log.ErrorContext(ctx, "Failed to lookup user", "filter", filter)
		return nil, err
	}

	return actor, nil
}

func (d *Database) LookupUserById(ctx context.Context, userId models.Uid) (*common.User, error) {
	filter := repo.Filter{Column: "id", Op: repo.Eq, Value: userId}
	return d.lookupUserQuery(ctx, filter)
}

func (d *Database) LookupUserByDid(ctx context.Context, did string) (*common.User, error) {
	filter := repo.Filter{Column: "did", Op: repo.Eq, Value: did}
	return d.lookupUserQuery(ctx, filter)
}

func (d *Database) LookupUserByHandle(ctx context.Context, handle string) (*common.User, error) {
	filter := repo.Filter{Column: "handle", Op: repo.Eq, Value: handle}
	return d.lookupUserQuery(ctx, filter)
}

func (d *Database) LookupUserByEmail(ctx context.Context, email string) (*common.User, error) {
	filter := repo.Filter{Column: "email", Op: repo.Eq, Value: email}
	return d.lookupUserQuery(ctx, filter)
}
