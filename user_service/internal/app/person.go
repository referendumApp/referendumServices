package app

import (
	"context"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

// GetProfile handler to querying the basic person profile
func (v *View) GetProfile(ctx context.Context, aid atp.Aid) (*atp.PersonBasic, *refErr.APIError) {
	profile, err := v.meta.GetPersonBasicProfile(ctx, aid)
	if err != nil {
		return nil, refErr.Database()
	}

	return profile, nil
}
