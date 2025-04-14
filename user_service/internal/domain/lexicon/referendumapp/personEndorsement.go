// Code generated by cmd/lexgen (see Makefile's lexgen); DO NOT EDIT.

package referendumapp

// schema: com.referendumapp.person.endorsement

import (
	comatproto "github.com/bluesky-social/indigo/api/atproto"
	"github.com/bluesky-social/indigo/lex/util"
	"github.com/bluesky-social/indigo/repo"
)

func init() {
	util.RegisterType("com.referendumapp.person.endorsement", &PersonEndorsement{})
}

// RECORDTYPE: PersonEndorsement
type PersonEndorsement struct {
	LexiconTypeID string                    `json:"$type" cborgen:"$type,const=com.referendumapp.person.endorsement" validate:"required"`
	CreatedAt     string                    `json:"createdAt" cborgen:"createdAt" validate:"required,datetime"`
	Subject       *comatproto.RepoStrongRef `json:"subject" cborgen:"subject" validate:"required"`
}

func (t PersonEndorsement) NSID() string {
	return "com.referendumapp.person.endorsement"
}

func (t PersonEndorsement) Key() string {
	return repo.NextTID()
}
