package app

import (
	"context"
	"errors"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

// GetBasicActorInformation handler to querying the basic user profile
func (v *View) GetBasicActorInformation(ctx context.Context, aid atp.Aid) (*atp.ActorBasic, *refErr.APIError) {
	actor, err := v.meta.GetActorBasic(ctx, aid, false)
	if err != nil {
		var apiErr *refErr.APIError
		if errors.As(err, &apiErr) {
			return nil, apiErr
		}

		return nil, refErr.Database()
	}

	return actor, nil
}
