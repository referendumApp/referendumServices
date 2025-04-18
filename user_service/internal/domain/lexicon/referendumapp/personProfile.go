// Code generated by cmd/lexgen (see Makefile's lexgen); DO NOT EDIT.

package referendumapp

// schema: com.referendumapp.person.profile

import (
	"github.com/bluesky-social/indigo/lex/util"
)

func init() {
	util.RegisterType("com.referendumapp.person.profile", &PersonProfile{})
}

// RECORDTYPE: PersonProfile
type PersonProfile struct {
	LexiconTypeID string `json:"$type" cborgen:"$type,const=com.referendumapp.person.profile" validate:"required"`
	// avatar: Small image to be displayed next to posts from account. AKA, 'profile picture'
	Avatar    *util.LexBlob `json:"avatar,omitempty" cborgen:"avatar,omitempty" validate:"omitempty"`
	CreatedAt *string       `json:"createdAt,omitempty" cborgen:"createdAt,omitempty" validate:"omitempty,datetime"`
	// description: Free-form profile description text.
	Description *string `json:"description,omitempty" cborgen:"description,omitempty" validate:"omitempty,max=2560"`
	DisplayName *string `json:"displayName,omitempty" cborgen:"displayName,omitempty" validate:"omitempty,max=640"`
}

func (t PersonProfile) NSID() string {
	return "com.referendumapp.person.profile"
}

func (t PersonProfile) Key() string {
	return "self"
}
