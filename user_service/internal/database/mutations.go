package database

import (
	"context"
	"errors"

	sq "github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5"
)

var ErrNoRowsAffected = errors.New("no rows affected")

type MutationFunc func(ctx context.Context, tx pgx.Tx) error

// WithTransaction executes any function within a db transaction
func (d *DB) WithTransaction(ctx context.Context, fn MutationFunc) error {
	conn, err := d.pool.Acquire(ctx)
	if err != nil {
		d.Log.ErrorContext(ctx, "Failed to acquire connection from db pool", "error", err)
		return err
	}
	defer conn.Release()

	tx, err := conn.Begin(ctx)
	if err != nil {
		d.Log.ErrorContext(ctx, "Failed to start transaction", "error", err)
		return err
	}
	defer func() {
		// If it's already committed, Rollback will be a no-op
		if err := tx.Rollback(ctx); err != nil && !errors.Is(err, pgx.ErrTxClosed) {
			// Log the error or update the return error if needed
			d.Log.ErrorContext(ctx, "Failed to rollback transaction", "error", err)
		}
	}()

	// Execute the callback function, passing the transaction
	if err := fn(ctx, tx); err != nil {
		return err
	}

	// Commit the transaction
	if err := tx.Commit(ctx); err != nil {
		d.Log.ErrorContext(ctx, "Failed to commit transaction", "error", err)
		return err
	}

	return nil
}

// TODO: Pretty sure we can combine all these non transaction methods into one method. But leaving for now for simplicities sake
func (d *DB) Create(ctx context.Context, entity TableEntity) error {
	query, err := BuildInsertQuery(entity, d.Schema)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building insert query", "error", err, "table", entity.TableName())
		return err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error creating raw insert query", "error", err, "table", entity.TableName())
		return err
	}

	if _, err := d.pool.Exec(ctx, sql, args...); err != nil {
		d.Log.ErrorContext(ctx, "Error executing statement", "error", err, "sql", sql)
		return err
	}

	return nil
}

func (d *DB) CreateBatch(ctx context.Context, entities []TableEntity) error {
	query, err := BuildBatchInsertQuery(entities, d.Schema)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building batch insert query", "error", err)
		return err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error creating raw batch insert query", "error", err)
		return err
	}

	if _, err := d.pool.Exec(ctx, sql, args...); err != nil {
		d.Log.ErrorContext(ctx, "Error executing statement", "error", err, "sql", sql)
		return err
	}

	return nil
}

func (d *DB) CreateConflict(ctx context.Context, entity TableEntity, conflictCol ...string) error {
	query, err := BuildInsertWithConflictQuery(entity, d.Schema, conflictCol...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building insert w/ conflict query", "error", err, "table", entity.TableName())
		return err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error creating raw insert w/ conflict query", "error", err, "table", entity.TableName())
		return err
	}

	if _, err := d.pool.Exec(ctx, sql, args...); err != nil {
		d.Log.ErrorContext(ctx, "Error executing statement", "error", err, "sql", sql)
		return err
	}

	return nil
}

func CreateReturning[T TableEntity](
	ctx context.Context,
	d *DB,
	entity T,
	returnCol ...string,
) (*T, error) {
	query, err := BuildInsertWithReturnQuery(entity, d.Schema, returnCol...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building insert w/ return query", "error", err, "table", entity.TableName())
		return nil, err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error creating raw insert w/ return query", "error", err, "table", entity.TableName())
		return nil, err
	}

	return Get[T](ctx, d, sql, args...)
}

func (d *DB) Update(ctx context.Context, entity TableEntity, idField string) error {
	query, err := BuildUpdateQuery(entity, d.Schema, idField)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building update query", "error", err, "table", entity.TableName())
		return err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error creating raw update query", "error", err, "table", entity.TableName())
		return err
	}

	tag, err := d.pool.Exec(ctx, sql, args...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error executing statement", "error", err, "sql", sql)
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrNoRowsAffected
	}

	return nil
}

func (d *DB) Delete(ctx context.Context, entity TableEntity, filters ...sq.Sqlizer) error {
	query, err := BuildDeleteQuery(entity, d.Schema, filters...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building delete query", "error", err, "table", entity.TableName())
		return err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error creating raw delete query", "error", err, "table", entity.TableName())
		return err
	}

	tag, err := d.pool.Exec(ctx, sql, args...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error executing statement", "error", err, "sql", sql)
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrNoRowsAffected
	}

	return nil
}

func (d *DB) CreateWithTx(ctx context.Context, tx pgx.Tx, entity TableEntity) error {
	query, err := BuildInsertQuery(entity, d.Schema)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building insert query in DB tx", "error", err, "table", entity.TableName())
		return err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error creating raw insert query in DB tx", "error", err, "table", entity.TableName())
		return err
	}

	if _, err := tx.Exec(ctx, sql, args...); err != nil {
		d.Log.ErrorContext(ctx, "Error executing statement in DB tx", "error", err, "sql", sql)
		return err
	}

	return nil
}

func (d *DB) CreateBatchWithTx(ctx context.Context, tx pgx.Tx, entities []TableEntity) error {
	query, err := BuildBatchInsertQuery(entities, d.Schema)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building batch insert query in DB tx", "error", err)
		return err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error creating raw batch insert query in DB tx", "error", err)
		return err
	}

	if _, err := tx.Exec(ctx, sql, args...); err != nil {
		d.Log.ErrorContext(ctx, "Error executing statement in DB tx", "error", err, "sql", sql)
		return err
	}

	return nil
}

func (d *DB) CreateConflictWithTx(
	ctx context.Context,
	tx pgx.Tx,
	entity TableEntity,
	conflictCol ...string,
) error {
	query, err := BuildInsertWithConflictQuery(entity, d.Schema, conflictCol...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building insert w/ conflict query in DB tx", "error", err, "table", entity.TableName())
		return err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error creating raw insert w/ conflict query in DB tx", "error", err, "table", entity.TableName())
		return err
	}

	if _, err := tx.Exec(ctx, sql, args...); err != nil {
		d.Log.ErrorContext(ctx, "Error executing statement in DB tx", "error", err, "sql", sql)
		return err
	}

	return nil
}

func CreateReturningWithTx[T TableEntity](
	ctx context.Context,
	d *DB,
	tx pgx.Tx,
	entity T,
	returnCol ...string,
) (*T, error) {
	query, err := BuildInsertWithReturnQuery(entity, d.Schema, returnCol...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building insert w/ return query in DB tx", "error", err, "table", entity.TableName())
		return nil, err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error compiling raw insert w/ return query in DB tx", "error", err, "table", entity.TableName())
		return nil, err
	}

	return GetWithTx[T](ctx, tx, sql, args...)
}

func (d *DB) UpdateWithTx(ctx context.Context, tx pgx.Tx, entity TableEntity, idField string) error {
	query, err := BuildUpdateQuery(entity, d.Schema, idField)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building update query in DB tx", "error", err, "table", entity.TableName())
		return err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error creating raw update query in DB tx", "error", err, "table", entity.TableName())
		return err
	}

	tag, err := tx.Exec(ctx, sql, args...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error executing statement in DB tx", "error", err, "sql", sql)
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrNoRowsAffected
	}

	return nil
}

func (d *DB) DeleteWithTx(ctx context.Context, tx pgx.Tx, entity TableEntity, filters ...sq.Sqlizer) error {
	query, err := BuildDeleteQuery(entity, d.Schema, filters...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building delete query in DB tx", "error", err, "table", entity.TableName())
		return err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error creating raw delete query in DB tx", "error", err, "table", entity.TableName())
		return err
	}

	tag, err := tx.Exec(ctx, sql, args...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error executing statement in DB tx", "error", err, "sql", sql)
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrNoRowsAffected
	}

	return nil
}
