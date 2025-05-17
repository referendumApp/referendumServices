package app

import (
	"context"
	"database/sql"
	"errors"

	sq "github.com/Masterminds/squirrel"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refApp "github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

// ResolveNewLegislator validates if the new legislator request can be handled
func (v *View) ResolveNewLegislator(ctx context.Context, req *refApp.ServerCreateLegislator_Input) *refErr.APIError {
	filter := sq.Eq{"legislator_id": req.LegislatorId}
	if exists, err := v.meta.legislatorExists(ctx, filter); err != nil {
		v.log.ErrorContext(ctx, "Error checking database for legislator_id", "error", err)
		return refErr.InternalServer()
	} else if exists {
		nerr := errors.New("legislator_id already exists")
		v.log.ErrorContext(ctx, nerr.Error(), "legislator_id", req.LegislatorId)
		fieldErr := refErr.FieldError{Field: "legislator_id", Message: nerr.Error()}
		return fieldErr.Conflict()
	}
	return nil
}

// SaveActorAndLegislator inserts a actor and legislator record to the DB
func (v *View) SaveActorAndLegislator(
	ctx context.Context,
	actor *atp.Actor,
	legislatorId int64,
) *refErr.APIError {
	if err := v.meta.insertActorAndLegislatorRecords(ctx, actor, legislatorId); err != nil {
		return refErr.Database()
	}
	return nil
}

// GetLegislator fetches the legislator record by either legislatorId or DID
func (v *View) GetLegislator(
	ctx context.Context,
	legislatorId *int64,
	did *string,
	handle *string,
) (*atp.Legislator, *refErr.APIError) {
	hasValidId := legislatorId != nil && *legislatorId != 0
	hasValidDid := did != nil && *did != ""
	hasValidHandle := handle != nil && *handle != ""

	var legislator *atp.Legislator
	var err error
	var lookupParam interface{}
	var lookupType string

	switch {
	case hasValidId:
		legislator, err = v.meta.LookupLegislatorByID(ctx, *legislatorId)
		lookupParam = *legislatorId
		lookupType = "ID"
	case hasValidHandle:
		legislator, err = v.meta.LookupLegislatorByHandle(ctx, *handle)
		lookupParam = *handle
		lookupType = "HANDLE"
	case hasValidDid:
		legislator, err = v.meta.LookupLegislatorByDid(ctx, *did)
		lookupParam = *did
		lookupType = "DID"
	default:
		v.log.ErrorContext(ctx, "Missing required parameter", "error", "legislator_id, did, or handle required")
		return nil, refErr.BadRequest("Required parameter not provided, needs one of: did, legislatorId, handle")
	}

	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			v.log.ErrorContext(ctx, "Legislator not found by "+lookupType, lookupType, lookupParam)
			return nil, refErr.NotFound(lookupParam, "Legislator")
		}
		v.log.ErrorContext(
			ctx,
			"Database error fetching legislator by "+lookupType,
			lookupType, lookupParam,
			"error", err,
		)
		return nil, refErr.Database()
	}

	return legislator, nil
}
