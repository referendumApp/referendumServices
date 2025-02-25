// Contains interface with HTTP validation methods

package models

import "context"

type Validator interface {
	Validate(ctx context.Context) (problems map[string]string)
}
