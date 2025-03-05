package database

import (
	"context"
	"database/sql"
	"fmt"
)

func (d *Database) GetUserId(ctx context.Context, email string) (int64, error) {
	var userId int64
	query := "SELECT id FROM users WHERE email = $1"

	stmt, err := d.conn.PrepareContext(ctx, query)
	if err != nil {
		return 0, fmt.Errorf("error preparing statement: %w", err)
	}
	defer stmt.Close()

	err = stmt.QueryRowContext(ctx, email).Scan(&userId)
	if err != nil {
		if err == sql.ErrNoRows {
			return 0, fmt.Errorf("no user found with email: %s", email)
		}

		return 0, fmt.Errorf("error querying user ID: %w", err)
	}

	return userId, nil
}

func (d *Database) BillExists(ctx context.Context, billId int64) (bool, error) {
	var exists bool
	query := "SELECT EXISTS(SELECT id FROM bills WHERE id = $1)"

	stmt, err := d.conn.PrepareContext(ctx, query)
	if err != nil {
		return false, fmt.Errorf("error preparing statement: %w", err)
	}
	defer stmt.Close()

	err = stmt.QueryRowContext(ctx, billId).Scan(&exists)
	if err != nil {
		return false, fmt.Errorf("error checking bill ID existence: %w", err)
	}

	return exists, nil
}
