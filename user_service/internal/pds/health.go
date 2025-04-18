package pds

import (
	"context"
	"net/http"
	"time"

	refErr "github.com/referendumApp/referendumServices/internal/error"
)

// HandleHealth s3 car store health check
func (p *PDS) HandleHealth(w http.ResponseWriter, r *http.Request) *refErr.APIError {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	if err := p.cs.PingStore(ctx); err != nil {
		return refErr.ServiceUnavailable()
	}

	return nil
}
