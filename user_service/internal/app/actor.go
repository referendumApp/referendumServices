package app

import (
	"context"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

// GetBasicActorInformation handler to querying the basic user profile
func (v *View) GetBasicActorInformation(ctx context.Context, aid atp.Aid) (*atp.ActorBasic, *refErr.APIError) {
	actor, err := v.meta.GetActorBasic(ctx, aid)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, refErr.NotFound("Actor %s not found", fmt.Sprintf("%d", aid))
		}
		return nil, refErr.Database()
	}
	return actor, nil
}
