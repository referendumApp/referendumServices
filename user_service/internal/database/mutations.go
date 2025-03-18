package database

import (
	"context"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"

	repo "github.com/referendumApp/referendumServices/internal/repository"
)

var ErrNoRowsAffected = errors.New("no rows affected")

type MutationFunc func(ctx context.Context, tx pgx.Tx) error

// WithTransaction executes any function within a db transaction
func (d *Database) WithTransaction(ctx context.Context, fn MutationFunc) error {
	conn, err := d.pool.Acquire(ctx)
	if err != nil {
		d.log.ErrorContext(ctx, "Failed to acquire connection from db pool", "error", err)
		return err
	}
	defer conn.Release()

	tx, err := conn.Begin(ctx)
	if err != nil {
		d.log.ErrorContext(ctx, "Failed to start transaction", "error", err)
		return err
	}
	defer func() {
		// If it's already committed, Rollback will be a no-op
		if err := tx.Rollback(ctx); err != nil && !errors.Is(err, pgx.ErrTxClosed) {
			// Log the error or update the return error if needed
			d.log.ErrorContext(ctx, "Failed to rollback transaction", "error", err)
		}
	}()

	// Execute the callback function, passing the transaction
	if err := fn(ctx, tx); err != nil {
		return err
	}

	// Commit the transaction
	if err := tx.Commit(ctx); err != nil {
		d.log.ErrorContext(ctx, "Failed to commit transaction", "error", err)
		return err
	}

	return nil
}

func (d *Database) PrepareAndExecute(
	ctx context.Context,
	tx pgx.Tx,
	name string,
	sql string,
	args []any,
) (*pgconn.CommandTag, error) {
	if _, err := tx.Prepare(ctx, name, sql); err != nil {
		d.log.ErrorContext(ctx, "Error preparing statement", "error", err)
		return nil, err
	}

	tag, err := tx.Exec(ctx, sql, args...)
	if err != nil {
		d.log.ErrorContext(ctx, "Error executing statement", "error", err)
		return nil, err
	}

	return &tag, nil
}

// TODO: Pretty sure we can combine all these non transaction methods into one method. But leaving for now for simplicities sake
func (d *Database) Create(ctx context.Context, entity repo.TableEntity) error {
	sql, args, err := repo.BuildInsertQuery(entity, d.schema)

	if err != nil {
		d.log.ErrorContext(ctx, "Error building insert query", "error", err, "table", entity.TableName())
		return err
	}

	if _, err := d.pool.Exec(ctx, sql, args...); err != nil {
		return err
	}

	return nil
}

func (d *Database) CreateWithConflict(ctx context.Context, entity repo.TableEntity, conflictCol ...string) error {
	sql, args, err := repo.BuildInsertWithConflictQuery(entity, d.schema, conflictCol...)
	if err != nil {
		d.log.ErrorContext(ctx, "Error building insert with conflict query", "error", err, "table", entity.TableName())
		return err
	}

	if _, err := d.pool.Exec(ctx, sql, args...); err != nil {
		return err
	}

	return nil
}

func CreateWithReturning[T repo.TableEntity](
	ctx context.Context,
	d *Database,
	entity T,
	returnCol ...string,
) (*T, error) {
	sql, args, err := repo.BuildInsertWithReturnQuery(entity, d.schema, returnCol...)
	if err != nil {
		d.log.ErrorContext(ctx, "Error building insert with returning query", "error", err, "table", entity.TableName())
		return nil, err
	}

	return Get[T](ctx, d, sql, args...)
}

func (d *Database) Update(ctx context.Context, entity repo.TableEntity, idField string) error {
	sql, args, err := repo.BuildUpdateQuery(entity, d.schema, idField)
	if err != nil {
		d.log.ErrorContext(ctx, "Error building update query", "error", err, "table", entity.TableName())
		return err
	}

	tag, err := d.pool.Exec(ctx, sql, args...)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrNoRowsAffected
	}

	return nil
}

func (d *Database) Delete(ctx context.Context, entity repo.TableEntity, filters ...repo.Filter) error {
	sql, args, err := repo.BuildDeleteQuery(entity, d.schema, filters...)
	if err != nil {
		d.log.ErrorContext(ctx, "Error building delete query", "error", err, "table", entity.TableName())
		return err
	}

	tag, err := d.pool.Exec(ctx, sql, args...)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrNoRowsAffected
	}

	return nil
}

func (d *Database) CreateWithTx(ctx context.Context, tx pgx.Tx, entity repo.TableEntity) error {
	name := fmt.Sprintf("create_%s", entity.TableName())
	sql, args, err := repo.BuildInsertQuery(entity, d.schema)

	if err != nil {
		d.log.ErrorContext(ctx, "Error building insert query", "error", err, "table", entity.TableName())
		return err
	}

	if _, err := d.PrepareAndExecute(ctx, tx, name, sql, args); err != nil {
		return err
	}

	return nil
}

func (d *Database) CreateWithConflictWithTx(
	ctx context.Context,
	tx pgx.Tx,
	entity repo.TableEntity,
	conflictCol ...string,
) error {
	name := fmt.Sprintf("create_conflict_%s", entity.TableName())
	sql, args, err := repo.BuildInsertWithConflictQuery(entity, d.schema, conflictCol...)
	if err != nil {
		d.log.ErrorContext(ctx, "Error building insert with conflict query", "error", err, "table", entity.TableName())
		return err
	}

	if _, err := d.PrepareAndExecute(ctx, tx, name, sql, args); err != nil {
		return err
	}

	return nil
}

func CreateWithReturningWithTx[T repo.TableEntity](
	ctx context.Context,
	d *Database,
	tx pgx.Tx,
	entity T,
	returnCol ...string,
) (*T, error) {
	sql, args, err := repo.BuildInsertWithReturnQuery(entity, d.schema, returnCol...)
	if err != nil {
		return nil, err
	}

	return GetWithTx[T](ctx, tx, sql, args...)
}

func (d *Database) UpdateWithTx(ctx context.Context, tx pgx.Tx, entity repo.TableEntity, idField string) error {
	name := fmt.Sprintf("update_%s", entity.TableName())
	sql, args, err := repo.BuildUpdateQuery(entity, d.schema, idField)
	if err != nil {
		d.log.ErrorContext(ctx, "Error building update query", "error", err, "table", entity.TableName())
		return err
	}

	tag, err := d.PrepareAndExecute(ctx, tx, name, sql, args)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrNoRowsAffected
	}

	return nil
}

func (d *Database) DeleteWithTx(ctx context.Context, tx pgx.Tx, entity repo.TableEntity, filters ...repo.Filter) error {
	name := fmt.Sprintf("delete_%s", entity.TableName())
	sql, args, err := repo.BuildDeleteQuery(entity, d.schema, filters...)
	if err != nil {
		d.log.ErrorContext(ctx, "Error building delete query", "error", err, "table", entity.TableName())
		return err
	}

	tag, err := d.PrepareAndExecute(ctx, tx, name, sql, args)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrNoRowsAffected
	}

	return nil
}
