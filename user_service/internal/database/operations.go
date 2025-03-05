package database

import (
	"context"
	"database/sql"
	"fmt"
	"log"

	"github.com/referendumApp/referendumServices/internal/domain/common"
)

func (d *Database) PrepareAndSelect(ctx context.Context, provider common.CRUDProvider) error {
	stmt, err := d.conn.PrepareNamedContext(ctx, provider.Query())
	if err != nil {
		return fmt.Errorf("error preparing %s statement: %w", common.OperationSelect, err)
	}
	defer stmt.Close()

	err = stmt.SelectContext(ctx, provider.GetResult(), provider)
	if err != nil {
		return fmt.Errorf("error executing query: %w", err)
	}

	return nil
}

func (d *Database) PrepareAndExecuteMutation(
	ctx context.Context,
	provider common.CRUDProvider,
	op common.Operation,
) (sql.Result, error) {
	var query string
	switch op {
	case common.OperationCreate:
		query = provider.Create()
	case common.OperationDelete:
		query = provider.Delete()
	default:
		return nil, fmt.Errorf("invalid database mutation operation: %s", op)
	}

	tx, err := d.conn.Beginx()
	if err != nil {
		return nil, fmt.Errorf("failed to start transaction: %w", err)
	}
	defer func() {
		// If it's already committed, Rollback will be a no-op
		if err = tx.Rollback(); err != nil && err != sql.ErrTxDone {
			// Log the error or update the return error if needed
			log.Printf("Failed to rollback transaction: %v", err)
		}
	}()

	stmt, err := tx.PrepareNamedContext(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("error preparing statement: %w", err)
	}
	defer stmt.Close()

	result, err := stmt.ExecContext(ctx, provider)
	if err != nil {
		return nil, fmt.Errorf("error executing statement: %w", err)
	}

	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %w", err)
	}

	return result, nil
}
