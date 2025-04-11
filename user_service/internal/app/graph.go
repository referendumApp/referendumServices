package app

import (
	"net/http"

	cbor "github.com/ipfs/go-ipld-cbor"

	"github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

func (v *View) HandleGraphFollowers(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	per, ok := util.GetAndValidatePerson(w, ctx, v.log)
	if !ok {
		return
	}

	followers, err := v.db.LookupUserGraphFollowers(ctx, per.Uid)
	if err != nil {
		refErr.Database().WriteResponse(w)
		return
	}

	ds, err := v.cs.ReadOnlySession(per.Uid)
	if err != nil {
		v.log.Error("Error creating read only session", "error", err, "id", per.Uid)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	var gf referendumapp.GraphFollow
	var fl []*referendumapp.GraphFollow
	for _, rec := range followers {
		nblk, err := ds.Get(ctx, rec.Cid.CID)
		if err != nil {
			v.log.ErrorContext(ctx, "Loading root from blockstore", "error", err)
			refErr.InternalServer().WriteResponse(w)
			return
		}

		if err := cbor.DecodeInto(nblk.RawData(), &gf); err != nil {
			v.log.Error("Error decoding follow block", "error", err, "id", per.Uid)
			refErr.InternalServer().WriteResponse(w)
			return
		}

		fl = append(fl, &gf)
	}

	util.Encode(w, http.StatusOK, v.log, fl)
}

func (v *View) HandleGraphFollowing(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	per, ok := util.GetAndValidatePerson(w, ctx, v.log)
	if !ok {
		return
	}

	following, err := v.db.LookupUserGraphFollowing(ctx, per.Uid)
	if err != nil {
		refErr.Database().WriteResponse(w)
		return
	}

	rev, err := v.cs.GetUserRepoRev(ctx, per.Uid)
	if err != nil {
		v.log.Error("Error repo head", "error", err, "id", per.Uid)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	ds, err := v.cs.NewDeltaSession(ctx, per.Uid, &rev)
	if err != nil {
		v.log.Error("Error creating read only session", "error", err, "id", per.Uid)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	var gf referendumapp.GraphFollow
	var fl []*referendumapp.GraphFollow
	for _, rec := range following {
		blk, err := ds.Get(ctx, rec.Cid.CID)
		if err != nil {
			v.log.Error("Error getting block", "error", err, "id", per.Uid)
			refErr.InternalServer().WriteResponse(w)
			return
		}

		if err := cbor.DecodeInto(blk.RawData(), &gf); err != nil {
			v.log.Error("Error decoding follow block", "error", err, "id", per.Uid)
			refErr.InternalServer().WriteResponse(w)
			return
		}

		fl = append(fl, &gf)
	}

	util.Encode(w, http.StatusOK, v.log, fl)
}
