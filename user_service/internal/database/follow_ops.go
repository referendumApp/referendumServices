package database

import (
	"context"
	"fmt"

	"github.com/bluesky-social/indigo/models"

	"github.com/referendumApp/referendumServices/internal/domain/common"
	"github.com/referendumApp/referendumServices/internal/domain/follow"
)

func (d *Database) BillExists(ctx context.Context, billId int64) (bool, error) {
	var exists bool
	query := "SELECT EXISTS(SELECT id FROM bills WHERE id = $1)"
	err := d.pool.QueryRow(ctx, query, billId).Scan(&exists)

	return exists, err
}

func (d *Database) GetUserFollowedBills(ctx context.Context, userID models.Uid) (*[]common.Bill, error) {
	var entity follow.UserFollowedBills

	sql := fmt.Sprintf(`SELECT bills.id, bills.legiscan_id, bills.identifier, bills.title, 
           bills.description, bills.state_id, bills.legislative_body_id, 
           bills.session_id, bills.status_id, bills.status_date, bills.current_version_id 
           FROM %s
           INNER JOIN bills ON user_bill_follows.bill_id = bills.id 
           WHERE user_id = $1`, entity.TableName())

	return Select[common.Bill](ctx, d, sql, userID)
}
