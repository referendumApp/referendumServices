package pds

import (
	"context"

	"github.com/ipfs/go-cid"
	cbg "github.com/whyrusleeping/cbor-gen"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

type Record interface {
	cbg.CBORMarshaler
	cbg.CBORUnmarshaler
	NSID() string
	Key() string
}

func (p *PDS) CreateRecord(ctx context.Context, uid atp.Uid, rec Record) (cid.Cid, string, *refErr.APIError) {
	cc, key, err := p.repoman.CreateRecord(ctx, uid, rec.NSID(), rec.Key(), rec)
	if err != nil {
		p.log.ErrorContext(ctx, "Error creating repo record", "error", err, "uid", uid, "record", rec)
		return cid.Undef, "", refErr.Repo()
	}

	return cc, key, nil
}

func (p *PDS) UpdateRecord(ctx context.Context, uid atp.Uid, rec Record) (cid.Cid, *refErr.APIError) {
	cc, err := p.repoman.UpdateRecord(ctx, uid, rec.NSID(), rec.Key(), rec)
	if err != nil {
		p.log.ErrorContext(ctx, "Error updating repo record", "error", err, "uid", uid, "record", rec)
		return cid.Undef, refErr.Repo()
	}

	return cc, nil
}

func (p *PDS) GetRecord(ctx context.Context, uid atp.Uid, rec Record) (cid.Cid, *refErr.APIError) {
	cc, err := p.repoman.GetRecord(ctx, uid, rec.NSID(), rec.Key(), rec, cid.Undef)
	if err != nil {
		p.log.ErrorContext(ctx, "Error getting repo record", "error", err, "uid", uid, "record", rec)
		return cid.Undef, refErr.Repo()
	}

	return cc, nil
}
