package follow

import "github.com/bluesky-social/indigo/models"

type UserFollowedBills struct {
	ID     int64      `db:"id,omitempty"`
	UserID models.Uid `db:"user_id"`
	BillID int64      `db:"bill_id"`
}

func (u UserFollowedBills) TableName() string {
	return "user_bill_follows"
}
