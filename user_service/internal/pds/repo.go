package pds

import (
	"context"
	"strings"

	"github.com/ipfs/go-cid"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/repo"
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
	// Use the repo manager's internal methods to check existence without unmarshaling
	bs, err := p.repoman.CarStore().ReadOnlySession(aid)
	if err != nil {
		p.log.ErrorContext(ctx, "Error getting read-only session", "error", err, "aid", aid)
		return false, refErr.Repo()
	}

	head, err := p.repoman.CarStore().GetActorRepoHead(ctx, aid)
	if err != nil {
		p.log.ErrorContext(ctx, "Error getting repo head", "error", err, "aid", aid)
		return false, refErr.Repo()
	}

	r, err := repo.OpenRepo(ctx, bs, head) // Note: you'll need to import the repo package
	if err != nil {
		p.log.ErrorContext(ctx, "Error opening repo", "error", err, "aid", aid)
		return false, refErr.Repo()
	}

	// Try to get just the CID and bytes without unmarshaling
	_, _, err = r.GetRecordBytes(ctx, nsid+"/"+rkey)
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
