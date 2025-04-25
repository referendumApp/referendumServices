package pds

import (
	"context"

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
func (p *PDS) CreateRecord(ctx context.Context, uid atp.Uid, rec Record) (cid.Cid, string, *refErr.APIError) {
	cc, key, err := p.repoman.CreateRecord(ctx, uid, rec.NSID(), rec.Key(), rec)
	if err != nil {
		p.log.ErrorContext(ctx, "Error creating repo record", "error", err, "uid", uid, "record", rec)
		return cid.Undef, "", refErr.Repo()
	}

	return cc, key, nil
}

// UpdateRecord 'Record' interface handler for updating a repo record
func (p *PDS) UpdateRecord(ctx context.Context, uid atp.Uid, rec Record) (cid.Cid, *refErr.APIError) {
	cc, err := p.repoman.UpdateRecord(ctx, uid, rec.NSID(), rec.Key(), rec)
	if err != nil {
		p.log.ErrorContext(ctx, "Error updating repo record", "error", err, "uid", uid, "record", rec)
		return cid.Undef, refErr.Repo()
	}

	return cc, nil
}

// GetRecord 'Record' interface handler for getting a repo record
func (p *PDS) GetRecord(ctx context.Context, uid atp.Uid, rec Record) (cid.Cid, *refErr.APIError) {
	cc, err := p.repoman.GetRecord(ctx, uid, rec.NSID(), rec.Key(), rec, cid.Undef)
	if err != nil {
		p.log.ErrorContext(ctx, "Error getting repo record", "error", err, "uid", uid, "record", rec)
		return cid.Undef, refErr.Repo()
	}

	return cc, nil
}
