// Code generated by cmd/lexgen (see Makefile's lexgen); DO NOT EDIT.

package referendumapp

// schema: com.referendumapp.bill.detail

import (
	comatproto "github.com/bluesky-social/indigo/api/atproto"
	"github.com/bluesky-social/indigo/lex/util"
	"github.com/referendumApp/referendumServices/internal/repo"
)

func init() {
	util.RegisterType("com.referendumapp.bill.detail", &BillDetail{})
}

// RECORDTYPE: BillDetail
type BillDetail struct {
	LexiconTypeID   string                    `json:"$type" cborgen:"$type,const=com.referendumapp.bill.detail" validate:"required"`
	CurrentVersion  *comatproto.RepoStrongRef `json:"currentVersion,omitempty" cborgen:"currentVersion,omitempty" validate:"omitempty"`
	Description     *string                   `json:"description,omitempty" cborgen:"description,omitempty" validate:"omitempty"`
	Identifier      string                    `json:"identifier" cborgen:"identifier" validate:"required"`
	Jurisdiction    string                    `json:"jurisdiction" cborgen:"jurisdiction" validate:"required"`
	LegislativeBody string                    `json:"legislativeBody" cborgen:"legislativeBody" validate:"required"`
	Session         string                    `json:"session" cborgen:"session" validate:"required"`
	Status          string                    `json:"status" cborgen:"status" validate:"required,oneof=Introduced,oneof=Passed,oneof=Vetoed,oneof=Failed,oneof=Prefiled,oneof=Engrossed,oneof=Enrolled,oneof=Override,oneof=Chaptered,oneof=Refer,oneof=Draft,oneof=Report Pass,oneof=Report DNP"`
	// statusDate: Client-declared timestamp when this post was originally created.
	StatusDate string   `json:"statusDate" cborgen:"statusDate" validate:"required,datetime"`
	Title      string   `json:"title" cborgen:"title" validate:"required"`
	Topic      []string `json:"topic,omitempty" cborgen:"topic,omitempty" validate:"omitempty"`
}

func (t BillDetail) NSID() string {
	return "com.referendumapp.bill.detail"
}

func (t BillDetail) Key() string {
	return repo.LID(t.Identifier, t.Session, t.Jurisdiction)
}
