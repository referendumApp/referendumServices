package database

import (
	"context"
	"fmt"

	sq "github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5"
)

// GetRowWithTx returns a scannable row within a transaction
func (d *DB) GetRowWithTx(ctx context.Context, tx pgx.Tx, sql string, args ...any) pgx.Row {
	return tx.QueryRow(ctx, sql, args...)
}

// GetRow returns a scannable row
func (d *DB) GetRow(ctx context.Context, sql string, args ...any) pgx.Row {
	return d.pool.QueryRow(ctx, sql, args...)
}

// GetWithTx returns a record within a transaction
func GetWithTx[T TableEntity](ctx context.Context, tx pgx.Tx, sql string, args ...any) (*T, error) {
	rows, err := tx.Query(ctx, sql, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	if !rows.Next() {
		if rows.Err() == nil {
			return nil, pgx.ErrNoRows
		}
		return nil, rows.Err()
	}

	result, err := pgx.RowToAddrOfStructByNameLax[T](rows)
	if err != nil {
		return nil, err
	}

	return result, rows.Err()
}

// Get returns a record
func Get[T TableEntity](ctx context.Context, d *DB, sql string, args ...any) (*T, error) {
	rows, err := d.pool.Query(ctx, sql, args...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error executing query", "error", err, "sql", sql)
		return nil, err
	}
	defer rows.Close()

	if !rows.Next() {
		if rows.Err() == nil {
			d.Log.WarnContext(ctx, "No rows found", "sql", sql)
			return nil, pgx.ErrNoRows
		}
		d.Log.ErrorContext(ctx, "Error iterating through rows", "error", rows.Err(), "sql", sql)
		return nil, rows.Err()
	}

	result, err := pgx.RowToAddrOfStructByNameLax[T](rows)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error scanning rows", "error", err, "sql", sql)
		return nil, err
	}

	return result, rows.Err()
}

// GetAll returns a record with all columns
func GetAll[T TableEntity](
	ctx context.Context,
	d *DB,
	entity T,
	filters ...sq.Sqlizer,
) (*T, error) {
	query, err := BuildSelectAll(entity, d.Schema, filters...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building select query", "error", err, "table", entity.TableName())
		return nil, err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error compiling raw select query", "error", err)
		return nil, err
	}

	return Get[T](ctx, d, sql, args...)
}

// Select returns all records
func Select[T TableEntity](ctx context.Context, d *DB, sql string, args ...any) ([]*T, error) {
	rows, err := d.pool.Query(ctx, sql, args...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error executing query", "error", err, "sql", sql)
		return nil, fmt.Errorf("error executing query: %w", err)
	}
	defer rows.Close()

	var result []*T

	for rows.Next() {
		row, err := pgx.RowToAddrOfStructByNameLax[T](rows)
		if err != nil {
			d.Log.ErrorContext(ctx, "Error scanning rows", "error", err, "sql", sql)
			return nil, err
		}

		result = append(result, row)
	}

	return result, rows.Err()
}

// SelectAll returns all records with all columns
func SelectAll[T TableEntity](
	ctx context.Context,
	d *DB,
	entity T,
	filters ...sq.Sqlizer,
) ([]*T, error) {
	query, err := BuildSelectAll(entity, d.Schema, filters...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building select query", "error", err, "table", entity.TableName())
		return nil, err
	}

	sql, args, err := query.ToSql()
	if err != nil {
		d.Log.ErrorContext(ctx, "Error compiling raw select query", "error", err)
		return nil, err
	}

	return Select[T](ctx, d, sql, args...)
}

// SelectLeft  returns all records with all columns from a left join
func SelectLeft[T TableEntity](
	ctx context.Context,
	d *DB,
	entity T,
	onLeft string,
	rightEnt TableEntity,
	onRight string,
	filters ...sq.Sqlizer,
) ([]*T, error) {
	leftTbl := d.Schema + "." + entity.TableName()
	rightTbl := d.Schema + "." + rightEnt.TableName()
	leftJoin := fmt.Sprintf("%s ON %s.%s = %s.%s", rightTbl, leftTbl, onLeft, rightTbl, onRight)

	query, err := BuildSelect(entity, d.Schema, filters...)
	if err != nil {
		d.Log.ErrorContext(ctx, "Error building select query", "error", err)
		return nil, err
	}

	sql, args, err := query.LeftJoin(leftJoin).ToSql()
	if err != nil {
		d.Log.ErrorContext(
			ctx,
			"Failed to compile left join select query",
			"error",
			err,
			"left",
			leftTbl,
			"right",
			rightTbl,
		)
		return nil, err
	}

	return Select[T](ctx, d, sql, args...)
}
