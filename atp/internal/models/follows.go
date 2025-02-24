package models

import "context"

type FollowRequest struct {
	UserMessage string `json:"userMessage"`
}

func (m *FollowRequest) Validate(ctx context.Context) (problems map[string]string) {
	problem := make(map[string]string, 1)

  if m.UserMessage == "" {
    problem["userMessage"] = "No value found"
  }

	return problem
}
