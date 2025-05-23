// Code generated by cmd/lexgen (see Makefile's lexgen); DO NOT EDIT.

package referendumapp

// schema: com.referendumapp.legislator.updateProfile

import (
	"github.com/bluesky-social/indigo/lex/util"
)

// LegislatorUpdateProfile_Input is the input argument to a com.referendumapp.legislator.updateProfile call.
type LegislatorUpdateProfile_Input struct {
	Address      *string       `json:"address,omitempty" cborgen:"address,omitempty" validate:"omitempty"`
	District     *string       `json:"district,omitempty" cborgen:"district,omitempty" validate:"omitempty"`
	Handle       *string       `json:"handle,omitempty" cborgen:"handle,omitempty" validate:"omitempty,handle"`
	Image        *util.LexBlob `json:"image,omitempty" cborgen:"image,omitempty" validate:"omitempty"`
	ImageUrl     *string       `json:"imageUrl,omitempty" cborgen:"imageUrl,omitempty" validate:"omitempty"`
	LegislatorId int64         `json:"legislatorId" cborgen:"legislatorId" validate:"required"`
	Legislature  *string       `json:"legislature,omitempty" cborgen:"legislature,omitempty" validate:"omitempty"`
	Name         *string       `json:"name,omitempty" cborgen:"name,omitempty" validate:"omitempty,name,max=60"`
	Party        *string       `json:"party,omitempty" cborgen:"party,omitempty" validate:"omitempty"`
	Phone        *string       `json:"phone,omitempty" cborgen:"phone,omitempty" validate:"omitempty,e164"`
	Role         *string       `json:"role,omitempty" cborgen:"role,omitempty" validate:"omitempty"`
	State        *string       `json:"state,omitempty" cborgen:"state,omitempty" validate:"omitempty"`
}

// LegislatorUpdateProfile_Output is the output of a com.referendumapp.legislator.updateProfile call.
//
// Account login session returned on successful account creation.
type LegislatorUpdateProfile_Output struct {
	Address      *string       `json:"address,omitempty" cborgen:"address,omitempty" validate:"omitempty"`
	District     *string       `json:"district,omitempty" cborgen:"district,omitempty" validate:"omitempty"`
	Handle       *string       `json:"handle,omitempty" cborgen:"handle,omitempty" validate:"omitempty,handle"`
	Image        *util.LexBlob `json:"image,omitempty" cborgen:"image,omitempty" validate:"omitempty"`
	ImageUrl     *string       `json:"imageUrl,omitempty" cborgen:"imageUrl,omitempty" validate:"omitempty"`
	LegislatorId *int64        `json:"legislatorId,omitempty" cborgen:"legislatorId,omitempty" validate:"omitempty"`
	Legislature  *string       `json:"legislature,omitempty" cborgen:"legislature,omitempty" validate:"omitempty"`
	Name         *string       `json:"name,omitempty" cborgen:"name,omitempty" validate:"omitempty,name,max=60"`
	Party        *string       `json:"party,omitempty" cborgen:"party,omitempty" validate:"omitempty"`
	Phone        *string       `json:"phone,omitempty" cborgen:"phone,omitempty" validate:"omitempty,e164"`
	Role         *string       `json:"role,omitempty" cborgen:"role,omitempty" validate:"omitempty"`
	State        *string       `json:"state,omitempty" cborgen:"state,omitempty" validate:"omitempty"`
}
