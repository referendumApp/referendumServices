package app

import (
	"net/http"

	"github.com/ipfs/go-cid"

	"github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

func (v *View) HandleGetProfile(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	per, ok := util.GetAndValidatePerson(w, ctx, v.log)
	if !ok {
		return
	}

	var prof referendumapp.PersonProfile
	if _, err := v.repoman.GetRecord(ctx, per.Uid, &prof, cid.Undef); err != nil {
		v.log.Error("Failed to get user profile", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	util.Encode(w, http.StatusOK, v.log, prof)
}
