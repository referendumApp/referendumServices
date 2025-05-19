// Package atp implements the AT Protocol data models and client functionality
package atp

import (
	"database/sql"
	"encoding/json"
	"time"

	"github.com/bluesky-social/indigo/xrpc"
)

// Aid represents an Actor ID, used as a primary identifier for actors in the system
type Aid uint64

// Base provides common fields for database models including timestamps and primary key
type Base struct {
	CreatedAt time.Time    `db:"created_at,omitempty" json:"-"`
	UpdatedAt time.Time    `db:"updated_at,omitempty" json:"-"`
	DeletedAt sql.NullTime `db:"deleted_at,omitempty" json:"-"`
	ID        uint         `db:"id,omitempty,pk"      json:"id"`
}

// Actor represents an authentication entity in the system and is the core account object that owns a repo
type Actor struct {
	Handle      sql.NullString `db:"handle,omitempty"       json:"-"`
	DisplayName sql.NullString `db:"display_name,omitempty" json:"display_name"`
	RecoveryKey string         `db:"recovery_key,omitempty" json:"-"`
	Did         string         `db:"did,omitempty"          json:"did"`
	CreatedAt   time.Time      `db:"created_at,omitempty"   json:"-"`
	UpdatedAt   time.Time      `db:"updated_at,omitempty"   json:"-"`
	DeletedAt   sql.NullTime   `db:"deleted_at,omitempty"   json:"-"`
	ID          Aid            `db:"id,omitempty,pk"        json:"id"`
	PDS         sql.NullInt64  `db:"pds_id,omitempty"       json:"-"`
	Settings    *Settings      `db:"settings,omitempty"     json:"settings"`
}

func (u Actor) TableName() string {
	return "actor"
}

type ActorBasic struct {
	ID          Aid          `db:"id,omitempty,pk"        json:"id"`
	Handle      *string      `db:"handle,omitempty"       json:"handle"`
	DisplayName string       `db:"display_name,omitempty" json:"display_name"`
	Did         string       `db:"did,omitempty"          json:"did"`
	DeletedAt   sql.NullTime `db:"deleted_at,omitempty"   json:"-"`
}

func (a ActorBasic) TableName() string {
	return "actor"
}

// Peering represents a peering relationship between servers
type Peering struct {
	Host string
	Did  string
	Base
	Approved bool
}

func (p Peering) TableName() string {
	return "peering"
}

// ActivityPost represents a post or content item in the activity stream
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

// Settings stores user configuration settings
type Settings struct {
	Type string `db:"type" json:"type"`
}

// Marshal serializes Settings to JSON
func (u *Settings) Marshal() ([]byte, error) {
	return json.Marshal(u)
}

// Unmarshal deserializes Settings from JSON
func (u *Settings) Unmarshal(data []byte) error {
	return json.Unmarshal(data, u)
}

// User represents the social profile in the system with display information and social metrics.
// Each User is associated with exactly one Actor via the Aid field.
type User struct {
	Base
	Did            string         `db:"did,omitempty"             json:"did"`
	Aid            Aid            `db:"aid,omitempty"             json:"-"`
	Following      int64          `db:"following,omitempty"       json:"following"`
	Followers      int64          `db:"followers,omitempty"       json:"followers"`
	Posts          int64          `db:"posts,omitempty"           json:"posts"`
	PDS            sql.NullInt64  `db:"pds_id,omitempty"          json:"-"`
	ValidHandle    bool           `db:"valid_handle,omitempty"    json:"valid_handle"`
	Email          sql.NullString `db:"email,omitempty"           json:"email"`
	HashedPassword sql.NullString `db:"hashed_password,omitempty" json:"-"`
}

func (a User) TableName() string {
	return "user"
}

// Legislator represents the legislator profile in the system
type Legislator struct {
	Base
	Did          string        `db:"did,omitempty"           json:"did"`
	Aid          Aid           `db:"aid,omitempty,pk"        json:"aid"`
	LegislatorId int64         `db:"legislator_id,omitempty" json:"-"`
	PDS          sql.NullInt64 `db:"pds_id,omitempty"        json:"-"`
}

func (u Legislator) TableName() string {
	return "legislator"
}

// EndorsementRecord represents a like or endorsement of a post
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

// ActorFollowRecord represents a follow relationship between actors
type ActorFollowRecord struct {
	Rkey string `db:"rkey"     json:"-"`
	Cid  DbCID  `db:"cid"      json:"-"`
	Base
	Follower Aid `db:"follower" json:"follower"`
	Target   Aid `db:"target"   json:"target"`
}

func (f ActorFollowRecord) TableName() string {
	return "actor_follow_record"
}

// PDS represents a Personal Data Server that hosts user data
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

// ClientForPds creates an xrpc client configured for a specific PDS
// It handles HTTP/HTTPS protocol selection based on the PDS configuration
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

// Feed represents a content feed with filtering criteria
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
