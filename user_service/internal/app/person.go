package app

import (
	"context"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

func (v *View) GetProfile(ctx context.Context, uid atp.Uid) (*atp.PersonBasic, *refErr.APIError) {
	profile, err := v.meta.GetPersonBasicProfile(ctx, uid)
	if err != nil {
		return nil, refErr.Database()
	}

	return profile, nil
}
