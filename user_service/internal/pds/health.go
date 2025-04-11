package pds

import (
	"context"
	"net/http"
	"time"

	"github.com/referendumApp/referendumServices/internal/util"
)

func (p *PDS) HandleHealth(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	resp := map[string]bool{"healthy": false}

	err := p.db.Ping(ctx)
	if err != nil {
		util.Encode(w, http.StatusServiceUnavailable, p.log, resp)
		return
	}

	resp["healthy"] = true
	util.Encode(w, http.StatusOK, p.log, resp)
}
