package car

import (
	"time"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
)

// Shard car_shards DB table schema
type Shard struct {
	CreatedAt time.Time `db:"created_at,omitempty" json:"-"`
	ID        uint      `db:"id,omitempty,pk"      json:"id"`

	Root      atp.DbCID `db:"root"       json:"root"`
	DataStart int64     `db:"data_start" json:"data_start"`
	Seq       int       `db:"seq"        json:"seq"`
	Path      string    `db:"path"       json:"path"`
	Aid       atp.Aid   `db:"aid"        json:"aid"`
	Rev       string    `db:"rev"        json:"rev"`
}

// TableName to implement DB interface
func (t Shard) TableName() string {
	return "car_shards"
}

// CompactionTarget querying the number of shards for each actor
type CompactionTarget struct {
	Actor     atp.Aid `db:"aid"`
	NumShards int     `db:"num_shards"`
}

// TableName to implement DB interface
func (t CompactionTarget) TableName() string {
	return "car_shards"
}

// BlockRef block_refs DB table schema
type BlockRef struct {
	ID         uint      `db:"id,omitempty,pk" json:"id"`
	Cid        atp.DbCID `db:"cid"             json:"cid"`
	Shard      uint      `db:"shard"           json:"shard"`
	ByteOffset int64     `db:"byte_offset"     json:"byte_offset"`
	Aid        atp.Aid   `db:"aid"             json:"aid"`
}

// TableName to implement DB interface
func (t BlockRef) TableName() string {
	return "block_refs"
}
