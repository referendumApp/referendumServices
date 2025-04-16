// Code generated by cmd/lexgen (see Makefile's lexgen); DO NOT EDIT.

package referendumapp

// schema: com.referendumapp.person.billFollow

import (
	comatproto "github.com/bluesky-social/indigo/api/atproto"
	"github.com/bluesky-social/indigo/lex/util"
	"github.com/referendumApp/referendumServices/internal/repo"
)

func init() {
	util.RegisterType("com.referendumapp.person.billFollow", &PersonBillFollow{})
}

// RECORDTYPE: PersonBillFollow
type PersonBillFollow struct {
	LexiconTypeID string                    `json:"$type" cborgen:"$type,const=com.referendumapp.person.billFollow" validate:"required"`
	Bill          *comatproto.RepoStrongRef `json:"bill" cborgen:"bill" validate:"required"`
	CreatedAt     string                    `json:"createdAt" cborgen:"createdAt" validate:"required,datetime"`
}

// PersonBillFollow_Input is the input argument to a com.referendumapp.person.billFollow call.
type PersonBillFollow_Input struct {
	// bid: Referendum bill ID (BID) to follow.
	Bid string `json:"bid" cborgen:"bid" validate:"required,bid"`
}

func (t PersonBillFollow) NSID() string {
	return "com.referendumapp.person.billFollow"
}

func (t PersonBillFollow) Key() string {
	return repo.NextTID()
}
