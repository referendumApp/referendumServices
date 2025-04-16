package app

import (
	"context"
	"net/http"
	"time"

	refErr "github.com/referendumApp/referendumServices/internal/error"
)

func (v *View) HandleHealth(w http.ResponseWriter, r *http.Request) (map[string]bool, *refErr.APIError) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	err := v.meta.Ping(ctx)
	if err != nil {
		return nil, refErr.ServiceUnavailable()
	}

	resp := map[string]bool{"healthy": true}
	return resp, nil
}
