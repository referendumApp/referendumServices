package follow

import "github.com/referendumApp/referendumServices/internal/domain/common"

type UserFollowedBills struct {
	Result *[]common.Bill `db:"-"`
	UserID int64          `db:"user_id"`
	BillID int64          `db:"bill_id"`
}

func (p UserFollowedBills) Create() string {
	return "INSERT INTO user_bill_follows (user_id, bill_id) VALUES (:user_id, :bill_id)"
}

func (p UserFollowedBills) Delete() string {
	return "DELETE FROM user_bill_follows WHERE user_id = :user_id AND bill_id = :bill_id"
}

func (p UserFollowedBills) Query() string {
	return `SELECT bills.id, bills.legiscan_id, bills.identifier, bills.title, 
           bills.description, bills.state_id, bills.legislative_body_id, 
           bills.session_id, bills.status_id, bills.status_date, bills.current_version_id 
           FROM user_bill_follows 
           INNER JOIN bills ON user_bill_follows.bill_id = bills.id 
           WHERE user_id = user_id`
}

func (p *UserFollowedBills) GetResult() any {
	if p.Result == nil {
		p.Result = &[]common.Bill{}
	}
	return p.Result
}
