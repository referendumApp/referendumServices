package common

import "time"

type Bill struct {
	StatusDate        time.Time `db:"status_date" json:"statusDate"`
	Identifier        string    `db:"identifier" json:"identifier"`
	Title             string    `db:"title" json:"title"`
	Description       string    `db:"description" json:"description"`
	ID                int64     `db:"id" json:"id"`
	CurrentVersionID  int64     `db:"current_version_id" json:"currentVersionId"`
	LegiscanID        int64     `db:"legiscan_id" json:"legiscanId"`
	LegislativeBodyID int64     `db:"legislative_body_id" json:"legislativeBodyId"`
	StateID           int64     `db:"state_id" json:"stateId"`
	StatusID          int64     `db:"status_id" json:"statusId"`
	SessionID         int64     `db:"session_id" json:"sessionId"`
}
