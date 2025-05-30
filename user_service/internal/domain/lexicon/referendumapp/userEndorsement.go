// Code generated by cmd/lexgen (see Makefile's lexgen); DO NOT EDIT.

package referendumapp

// schema: com.referendumapp.user.endorsement

import (
	comatproto "github.com/bluesky-social/indigo/api/atproto"
	"github.com/bluesky-social/indigo/lex/util"
	"github.com/referendumApp/referendumServices/internal/repo"
)

func init() {
	util.RegisterType("com.referendumapp.user.endorsement", &UserEndorsement{})
}

// RECORDTYPE: UserEndorsement
type UserEndorsement struct {
	LexiconTypeID string                    `json:"$type" cborgen:"$type,const=com.referendumapp.user.endorsement" validate:"required"`
	CreatedAt     string                    `json:"createdAt" cborgen:"createdAt" validate:"required,datetime"`
	Subject       *comatproto.RepoStrongRef `json:"subject" cborgen:"subject" validate:"required"`
}

func (t UserEndorsement) NSID() string {
	return "com.referendumapp.user.endorsement"
}

func (t UserEndorsement) Key() string {
	return repo.NextTID()
}
