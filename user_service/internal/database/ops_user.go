package database

import (
	"context"
	"fmt"

	sq "github.com/Masterminds/squirrel"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
)

func (d *DB) UserExists(ctx context.Context, field string, value any) (bool, error) {
	var exists bool
	sql := fmt.Sprintf("SELECT EXISTS(SELECT id FROM %s.user WHERE %s = $1)", d.Schema, field)
	err := d.GetRow(ctx, sql, value).Scan(&exists)
	return exists, err
}

func (d *DB) AuthenticateUser(ctx context.Context, email string) (*atp.User, error) {
	var user atp.User
	sql := fmt.Sprintf("SELECT id, did, handle, hashed_password FROM %s.%s WHERE email = $1", d.Schema, user.TableName())

	if err := d.GetRow(ctx, sql, email).Scan(&user.ID, &user.Did, &user.Handle, &user.HashedPassword); err != nil {
		return nil, err
	}

	return &user, nil
}

func (d *DB) AuthenticateHandle(ctx context.Context, user *atp.User) (bool, error) {
	var exists bool
	sql := fmt.Sprintf("SELECT EXISTS(SELECT id FROM %s.%s WHERE email != $1 AND handle = $2)", d.Schema, user.TableName())
	err := d.GetRow(ctx, sql, user.Email, user.Handle).Scan(&exists)

	return exists, err
}

func (d *DB) lookupUserQuery(ctx context.Context, filter sq.Sqlizer) (*atp.User, error) {
	var entity atp.User
	user, err := GetAll(ctx, d, entity, filter)
	if err != nil {
		d.Log.ErrorContext(ctx, "Failed to lookup user", "filter", filter)
		return nil, err
	}

	return user, nil
}

func (d *DB) LookupUserById(ctx context.Context, userId atp.Uid) (*atp.User, error) {
	filter := sq.Eq{"id": userId}
	return d.lookupUserQuery(ctx, filter)
}

func (d *DB) LookupUserByDid(ctx context.Context, did string) (*atp.User, error) {
	filter := sq.Eq{"did": did}
	return d.lookupUserQuery(ctx, filter)
}

func (d *DB) LookupUserByHandle(ctx context.Context, handle string) (*atp.User, error) {
	filter := sq.Eq{"handle": handle}
	return d.lookupUserQuery(ctx, filter)
}

func (d *DB) LookupUserByEmail(ctx context.Context, email string) (*atp.User, error) {
	filter := sq.Eq{"email": email}
	return d.lookupUserQuery(ctx, filter)
}
