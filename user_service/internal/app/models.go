package app

import (
	"database/sql"
	"fmt"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
)

type actorAuth struct {
	actorProfile
	AuthSettings *atp.AuthSettings `db:"auth_settings,omitempty" join:"left"`
}

type actorProfile struct {
	DisplayName string         `db:"display_name,omitempty" join:"right"`
	Did         string         `db:"did,omitempty"          join:"left"`
	ID          atp.Aid        `db:"id,omitempty"           join:"left"`
	Handle      sql.NullString `db:"handle,omitempty"       join:"left"`
	Email       sql.NullString `db:"email,omitempty"        join:"left"`
}

func (a actorProfile) LeftTable() string {
	return "actors"
}

func (a actorProfile) RightTable() string {
	return "users"
}

func (a actorProfile) On() string {
	return fmt.Sprintf("%s.id = %s.aid", a.LeftTable(), a.RightTable())
}

type publicServantIDs struct {
	Did string  `db:"did,omitempty"`
	Aid atp.Aid `db:"aid,omitempty"`
}

func (p publicServantIDs) TableName() string {
	return "public_servants"
}
