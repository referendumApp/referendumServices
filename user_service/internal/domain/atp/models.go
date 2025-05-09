//revive:disable:exported
package atp

import (
	"database/sql"
	"encoding/json"
	"time"

	"github.com/bluesky-social/indigo/xrpc"
)

type Aid uint64

type Base struct {
	CreatedAt time.Time    `db:"created_at,omitempty" json:"-"`
	UpdatedAt time.Time    `db:"updated_at,omitempty" json:"-"`
	DeletedAt sql.NullTime `db:"deleted_at,omitempty" json:"-"`
	ID        uint         `db:"id,omitempty,pk"      json:"id"`
}

type Actor struct {
	Email          sql.NullString `db:"email,omitempty"           json:"email"`
	HashedPassword sql.NullString `db:"hashed_password,omitempty" json:"-"`
	Handle         sql.NullString `db:"handle,omitempty"          json:"-"`
	RecoveryKey    string         `db:"recovery_key,omitempty"    json:"-"`
	Did            string         `db:"did,omitempty"             json:"did"`
	CreatedAt      time.Time      `db:"created_at,omitempty"      json:"-"`
	UpdatedAt      time.Time      `db:"updated_at,omitempty"      json:"-"`
	DeletedAt      sql.NullTime   `db:"deleted_at,omitempty"      json:"-"`
	ID             Aid            `db:"id,omitempty,pk"           json:"id"`
	PDS            sql.NullInt64  `db:"pds_id,omitempty"          json:"-"`
}

func (u Actor) TableName() string {
	return "actor"
}

type Peering struct {
	Host string
	Did  string
	Base
	Approved bool
}

func (p Peering) TableName() string {
	return "peering"
}

type ActivityPost struct {
	Rkey string `db:"rkey"         json:"-"`
	Cid  DbCID  `db:"cid"          json:"-"`
	Base
	Author       Aid   `db:"author"       json:"author"`
	Endorsements int64 `db:"endorsements" json:"endorsements"`
	ReplyCount   int64 `db:"reply_count"  json:"reply_count"`
	ReplyTo      uint  `db:"reply_to"     json:"reply_to"`
	Missing      bool  `db:"missing"      json:"missing"`
	Deleted      bool  `db:"deleted"      json:"deleted"`
}

func (f ActivityPost) TableName() string {
	return "activity_post"
}

type Settings struct {
	Deleted bool `db:"deleted" json:"deleted"`
}

func (u *Settings) Marshal() ([]byte, error) {
	return json.Marshal(u)
}

func (u *Settings) Unmarshal(data []byte) error {
	return json.Unmarshal(data, u)
}

type Person struct {
	Settings    *Settings      `db:"settings,omitempty"     json:"settings"`
	Handle      sql.NullString `db:"handle,omitempty"       json:"handle"`
	DisplayName string         `db:"display_name,omitempty" json:"display_name"`
	Did         string         `db:"did,omitempty"          json:"did"`
	Type        sql.NullString `db:"type,omitempty"         json:"type"`
	Base
	Aid         Aid           `db:"uid,omitempty"          json:"-"`
	Following   int64         `db:"following,omitempty"    json:"following"`
	Followers   int64         `db:"followers,omitempty"    json:"followers"`
	Posts       int64         `db:"posts,omitempty"        json:"posts"`
	PDS         sql.NullInt64 `db:"pds_id,omitempty"       json:"-"`
	ValidHandle bool          `db:"valid_handle,omitempty" json:"valid_handle"`
}

func (a Person) TableName() string {
	return "person"
}

type PersonBasic struct {
	Handle      *string `db:"handle,omitempty"       json:"handle"`
	DisplayName string  `db:"display_name,omitempty" json:"display_name"`
	Did         string  `db:"did,omitempty"          json:"did"`
	Type        *string `db:"type,omitempty"         json:"type"`
}

func (a PersonBasic) TableName() string {
	return "person"
}

type EndorsementRecord struct {
	Created  string `db:"created"         json:"-"`
	Rkey     string `db:"rkey"            json:"-"`
	Cid      DbCID  `db:"cid"             json:"-"`
	Endorser Aid    `db:"endorser"        json:"endorser"`
	ID       uint   `db:"id,omitempty,pk" json:"id"`
	Post     uint   `db:"post_id"         json:"post"`
}

func (v EndorsementRecord) TableName() string {
	return "endorsement_record"
}

type UserFollowRecord struct {
	Rkey string `db:"rkey"     json:"-"`
	Cid  DbCID  `db:"cid"      json:"-"`
	Base
	Follower Aid `db:"follower" json:"follower"`
	Target   Aid `db:"target"   json:"target"`
}

func (f UserFollowRecord) TableName() string {
	return "user_follow_record"
}

type PDS struct {
	Host string `db:"host"`
	Did  string `db:"did"`
	Base
	Cursor           int64   `db:"cursor"`
	RepoCount        int64   `db:"repo_count"`
	RepoLimit        int64   `db:"repo_limit"`
	HourlyEventLimit int64   `db:"hourly_event_limit"`
	DailyEventLimit  int64   `db:"daily_event_limit"`
	SSL              bool    `db:"ssl"`
	Registered       bool    `db:"registered"`
	Blocked          bool    `db:"blocked"`
	RateLimit        float64 `db:"rate_limit"`
	CrawlRateLimit   float64 `db:"crawl_rate_limit"`
}

func (p PDS) TableName() string {
	return "pds"
}

func ClientForPds(pds *PDS) *xrpc.Client {
	if pds.SSL {
		return &xrpc.Client{
			Host: "https://" + pds.Host,
		}
	}
	return &xrpc.Client{
		Host: "http://" + pds.Host,
	}
}

// type DomainBan struct {
// 	Base
// 	Domain string `db:"domain"`
// }
//
// func (d DomainBan) TableName() string {
// 	return "domain_ban"
// }

type Feed struct {
	ID           uint      `db:"id,omitempty,pk"        json:"id"`
	IndexedAt    time.Time `db:"indexed_at,omitempty"   json:"-"`
	Rkey         string    `db:"rkey"                   json:"-"`
	Cid          DbCID     `db:"cid"                    json:"-"`
	Jurisdiction string    `db:"jurisdiction,omitempty" json:"jurisdiction"`
	Topic        []string  `db:"topic,omitempty"        json:"topic"`
	Type         string    `db:"type"                   json:"type"`
}

func (p Feed) TableName() string {
	return "feed"
}
