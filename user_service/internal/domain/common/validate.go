// Contains interface with HTTP validation methods

package common

import (
	"context"

	refErr "github.com/referendumApp/referendumServices/internal/error"
)

type Validator interface {
	Validate(ctx context.Context) *refErr.APIError
}
