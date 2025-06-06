package pds

import (
	"context"
	"strings"

	"github.com/ipfs/go-cid"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	cbg "github.com/whyrusleeping/cbor-gen"
)

// Record method signatures for a repo record
type Record interface {
	cbg.CBORMarshaler
	cbg.CBORUnmarshaler
	NSID() string
	Key() string
}

// CreateRecord 'Record' interface handler for creating a repo record
func (p *PDS) CreateRecord(ctx context.Context, aid atp.Aid, rec Record) (cid.Cid, string, *refErr.APIError) {
	cc, key, err := p.repoman.CreateRecord(ctx, aid, rec.NSID(), rec.Key(), rec)
	if err != nil {
		p.log.ErrorContext(ctx, "Error creating repo record", "error", err, "aid", aid, "record", rec)
		return cid.Undef, "", refErr.Repo()
	}

	return cc, key, nil
}

// UpdateRecord 'Record' interface handler for updating a repo record
func (p *PDS) UpdateRecord(ctx context.Context, aid atp.Aid, rec Record) (cid.Cid, *refErr.APIError) {
	cc, err := p.repoman.UpdateRecord(ctx, aid, rec.NSID(), rec.Key(), rec)
	if err != nil {
		p.log.ErrorContext(ctx, "Error updating repo record", "error", err, "aid", aid, "record", rec)
		if strings.Contains(err.Error(), "could not find record with key:") {
			return cid.Undef, refErr.NotFound(rec.Key(), rec.NSID())
		}
		return cid.Undef, refErr.Repo()
	}

	return cc, nil
}

// DeleteRecord 'Record' interface handler for deleting a repo record
func (p *PDS) DeleteRecord(ctx context.Context, aid atp.Aid, collection string, rkey string) *refErr.APIError {
	if err := p.repoman.DeleteRecord(ctx, aid, collection, rkey); err != nil {
		p.log.ErrorContext(ctx, "Error deleting repo record", "error", err, "nsid", collection, "rkey", rkey)
		if strings.Contains(err.Error(), "could not find record with key:") {
			return refErr.NotFound(rkey, collection)
		}
		return refErr.Repo()
	}

	return nil
}

// GetRecord 'Record' interface handler for getting a repo record
func (p *PDS) GetRecord(ctx context.Context, aid atp.Aid, rec Record) (cid.Cid, *refErr.APIError) {
	cc, err := p.repoman.GetRecord(ctx, aid, rec.NSID(), rec.Key(), rec, cid.Undef)
	p.log.InfoContext(ctx, "Got record", "cid", cc, "err", err)
	if err != nil {
		p.log.ErrorContext(ctx, "Error getting repo record", "error", err, "aid", aid, "record", rec)
		if strings.Contains(err.Error(), "could not find record with key:") {
			return cid.Undef, refErr.NotFound(rec.Key(), rec.NSID())
		}
		return cid.Undef, refErr.Repo()
	}
	return cc, nil
}

// RecordExists checks if a record exists without requiring a fully validated record instance
func (p *PDS) RecordExists(
	ctx context.Context,
	aid atp.Aid,
	nsid string,
	rkey string,
) (bool, *refErr.APIError) {
	_, err := p.repoman.GetRecord(ctx, aid, nsid, rkey, nil, cid.Undef)
	if err != nil {
		if strings.Contains(err.Error(), "mst: not found") {
			return false, nil
		}
		if strings.Contains(err.Error(), "could not find record with key:") {
			return false, nil
		}
		p.log.ErrorContext(
			ctx, "Error checking record existence",
			"error", err,
			"aid", aid,
			"nsid", nsid,
			"rkey", rkey,
		)
		return false, refErr.Repo()
	}
	return true, nil
}
