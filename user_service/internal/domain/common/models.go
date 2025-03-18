package common

import (
	"database/sql"
	"time"

	"github.com/bluesky-social/indigo/models"
)

type User struct {
	Name           string        `db:"name,omitempty" json:"name"`
	Email          string        `db:"email,omitempty" json:"email"`
	HashedPassword string        `db:"hashed_password,omitempty" json:"-"`
	Handle         string        `db:"handle,omitempty" json:"-"`
	RecoveryKey    string        `db:"recovery_key,omitempty" json:"-"`
	Did            string        `db:"did,omitempty" json:"-"`
	CreatedAt      time.Time     `db:"created_at,omitempty" json:"-"`
	UpdatedAt      time.Time     `db:"updated_at,omitempty" json:"-"`
	DeletedAt      sql.NullTime  `db:"deleted_at,omitempty" json:"-"`
	ID             models.Uid    `db:"id,omitempty,pk" json:"id"`
	PDS            sql.NullInt64 `db:"pds_id,omitempty" json:"-"`
}

func (u User) TableName() string {
	return "user"
}

type Bill struct {
	StatusDate        time.Time `db:"status_date" json:"statusDate"`
	Identifier        string    `db:"identifier" json:"identifier"`
	Title             string    `db:"title" json:"title"`
	Description       string    `db:"description" json:"description"`
	ID                int64     `db:"id,pk" json:"id"`
	CurrentVersionID  int64     `db:"current_version_id" json:"currentVersionId"`
	LegiscanID        int64     `db:"legiscan_id" json:"legiscanId"`
	LegislativeBodyID int64     `db:"legislative_body_id" json:"legislativeBodyId"`
	StateID           int64     `db:"state_id" json:"stateId"`
	StatusID          int64     `db:"status_id" json:"statusId"`
	SessionID         int64     `db:"session_id" json:"sessionId"`
}

func (b Bill) TableName() string {
	return "bills"
}
