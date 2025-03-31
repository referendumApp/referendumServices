package database

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5"

	repo "github.com/referendumApp/referendumServices/internal/repository"
)

func GetWithTx[T repo.TableEntity](ctx context.Context, tx pgx.Tx, sql string, args ...any) (*T, error) {
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

func Get[T repo.TableEntity](ctx context.Context, d *Database, sql string, args ...any) (*T, error) {
	rows, err := d.pool.Query(ctx, sql, args...)
	if err != nil {
		d.log.ErrorContext(ctx, "Error executing query", "error", err, "sql", sql, "args", args)
		return nil, err
	}
	defer rows.Close()

	if !rows.Next() {
		if rows.Err() == nil {
			d.log.WarnContext(ctx, "No rows found", "sql", sql, "args", args)
			return nil, pgx.ErrNoRows
		}
		d.log.ErrorContext(ctx, "Error iterating through rows", "error", rows.Err(), "sql", sql, "args", args)
		return nil, rows.Err()
	}

	result, err := pgx.RowToAddrOfStructByNameLax[T](rows)
	if err != nil {
		d.log.ErrorContext(ctx, "Error scanning rows", "error", err, "sql", sql, "args", args)
		return nil, err
	}

	return result, rows.Err()
}

func GetAll[T repo.TableEntity](
	ctx context.Context,
	d *Database,
	entity T,
	filters ...repo.Filter,
) (*T, error) {
	sql, args, err := repo.BuildSelectAll(entity, d.schema, filters...)
	if err != nil {
		d.log.ErrorContext(ctx, "Error building select query", "error", err, "table", entity.TableName(), "filters", filters)
		return nil, err
	}
	return Get[T](ctx, d, sql, args...)
}

func Select[T repo.TableEntity](ctx context.Context, d *Database, sql string, args ...any) (*[]T, error) {
	rows, err := d.pool.Query(ctx, sql, args...)
	if err != nil {
		d.log.ErrorContext(ctx, "Error executing query", "error", err, "sql", sql, "args", args)
		return nil, fmt.Errorf("error executing query: %w", err)
	}
	defer rows.Close()

	var result []T

	for rows.Next() {
		row, err := pgx.RowToStructByName[T](rows)
		if err != nil {
			d.log.ErrorContext(ctx, "Error scanning rows", "error", err, "sql", sql, "args", args)
			return nil, err
		}

		result = append(result, row)
	}

	return &result, rows.Err()
}

func SelectAll[T repo.TableEntity](
	ctx context.Context,
	d *Database,
	entity T,
	filters ...repo.Filter,
) (*[]T, error) {
	sql, args, err := repo.BuildSelectAll(entity, d.schema, filters...)
	if err != nil {
		d.log.ErrorContext(ctx, "Error building select query", "error", err, "table", entity.TableName(), "filters", filters)
		return nil, err
	}
	return Select[T](ctx, d, sql, args...)
}
