// Contains structs for the `follows` HTTP request and response bodies and Validate implementations

package follow

import "context"

type BillRequest struct {
	UserMessage string `json:"userMessage"`
}

func (m *BillRequest) Validate(ctx context.Context) (problems map[string]string) {
	problem := make(map[string]string, 1)

	if m.UserMessage == "" {
		problem["userMessage"] = "No value found"
	}

	return problem
}
