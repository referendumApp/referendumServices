package models

import "context"

type Validator interface {
	Validate(ctx context.Context) (problems map[string]string)
}
