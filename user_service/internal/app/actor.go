package app

import (
	"context"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

// GetBasicActorInformation handler to querying the basic user profile
func (v *View) GetBasicActorInformation(ctx context.Context, aid atp.Aid) (*atp.ActorBasic, *refErr.APIError) {
	actor, err := v.meta.GetActorBasic(ctx, aid)
	if err != nil {
		return nil, refErr.Database()
	}

	return actor, nil
}
