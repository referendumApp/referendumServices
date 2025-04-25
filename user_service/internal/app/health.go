package app

import (
	"context"
	"net/http"
	"time"

	refErr "github.com/referendumApp/referendumServices/internal/error"
)

// HandleHealth database health check
func (v *View) HandleHealth(w http.ResponseWriter, r *http.Request) *refErr.APIError {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	err := v.meta.Ping(ctx)
	if err != nil {
		return refErr.ServiceUnavailable()
	}

	return nil
}
