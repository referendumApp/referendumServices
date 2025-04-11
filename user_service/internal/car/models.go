package car

import (
	"bytes"
	"io"
	"time"

	"github.com/ipfs/go-cid"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
)

type Shard struct {
	CreatedAt time.Time `db:"created_at,omitempty" json:"-"`
	ID        uint      `db:"id,omitempty,pk" json:"id"`

	Root      atp.DbCID `db:"root" json:"root"`
	DataStart int64     `db:"data_start" json:"data_start"`
	Seq       int       `db:"seq" json:"seq"`
	Path      string    `db:"path" json:"path"`
	Uid       atp.Uid   `db:"uid" json:"uid"`
	Rev       string    `db:"rev" json:"rev"`
}

func (t Shard) TableName() string {
	return "car_shards"
}

type BlockRef struct {
	ID         uint      `db:"id,omitempty,pk" json:"id"`
	Cid        atp.DbCID `db:"cid" json:"cid"`
	Shard      uint      `db:"shard" json:"shard"`
	ByteOffset int64     `db:"byte_offset" json:"byte_offset"`
	Uid        atp.Uid   `db:"uid" json:"uid"`
}

func (t BlockRef) TableName() string {
	return "block_refs"
}

type StaleRef struct {
	ID   uint       `db:"id,omitempty,pk" json:"id"`
	Cid  *atp.DbCID `db:"cid" json:"cid"`
	Cids []byte     `db:"cids" json:"cids"`
	Uid  atp.Uid    `db:"uid" json:"uid"`
}

func (t StaleRef) TableName() string {
	return "stale_refs"
}

func (sr *StaleRef) getCids() ([]cid.Cid, error) {
	if sr.Cid != nil {
		return []cid.Cid{sr.Cid.CID}, nil
	}

	return unpackCids(sr.Cids)
}

func unpackCids(b []byte) ([]cid.Cid, error) {
	br := bytes.NewReader(b)
	var out []cid.Cid
	for {
		_, c, err := cid.CidFromReader(br)
		if err != nil {
			if err == io.EOF {
				break
			}
			return nil, err
		}

		out = append(out, c)
	}

	return out, nil
}
