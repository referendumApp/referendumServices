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

// Metadata provides common datetime fields for database models
type Metadata struct {
	CreatedAt time.Time    `db:"created_at,omitempty"`
	UpdatedAt time.Time    `db:"updated_at,omitempty"`
	DeletedAt sql.NullTime `db:"deleted_at,omitempty"`
}

// Base provides common fields for database models including timestamps and primary key
type Base struct {
	Metadata
	ID uint `db:"id,omitempty,pk"`
}

// AuthSettings stores authentication configuration
type AuthSettings struct {
	HashedPassword string `json:"hashed_password,omitempty"`
	ApiKey         string `json:"api_key,omitempty"`
}

// Marshal serializes Settings to JSON
func (u *AuthSettings) Marshal() ([]byte, error) {
	return json.Marshal(u)
}

// Unmarshal deserializes Settings from JSON
func (u *AuthSettings) Unmarshal(data []byte) error {
	return json.Unmarshal(data, u)
}

// Actor is the core account object that owns a repo and contains auth information
type Actor struct {
	Handle      sql.NullString `db:"handle,omitempty"`
	RecoveryKey string         `db:"recovery_key,omitempty"`
	Did         string         `db:"did,omitempty"`
	Metadata
	ID           Aid            `db:"id,omitempty,pk"`
	PDS          sql.NullInt64  `db:"pds_id,omitempty"`
	Email        sql.NullString `db:"email,omitempty"`
	AuthSettings *AuthSettings  `db:"auth_settings,omitempty"`
}

func (u Actor) TableName() string {
	return "actors"
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
	Rkey string `db:"rkey"`
	Cid  DbCID  `db:"cid"`
	Base
	Author       Aid   `db:"author"`
	Endorsements int64 `db:"endorsements"`
	ReplyCount   int64 `db:"reply_count"`
	ReplyTo      uint  `db:"reply_to"`
	Missing      bool  `db:"missing"`
	Deleted      bool  `db:"deleted"`
}

func (f ActivityPost) TableName() string {
	return "activity_post"
}

// UserSettings stores user configuration settings
type UserSettings struct {
	Type string `json:"type"`
}

func (u *UserSettings) Marshal() ([]byte, error) {
	return json.Marshal(u)
}

func (u *UserSettings) Unmarshal(data []byte) error {
	return json.Unmarshal(data, u)
}

// User represents the social profile in the system with display information and social metrics.
// Each User is associated with exactly one Actor via the Aid field.
type User struct {
	Base
	Did         string        `db:"did,omitempty"`
	Aid         Aid           `db:"aid,omitempty"`
	DisplayName string        `db:"display_name,omitempty"`
	Following   int64         `db:"following,omitempty"`
	Followers   int64         `db:"followers,omitempty"`
	Posts       int64         `db:"posts,omitempty"`
	PDS         sql.NullInt64 `db:"pds_id,omitempty"`
	ValidHandle bool          `db:"valid_handle,omitempty"`
	Settings    *UserSettings `db:"settings,omitempty"`
}

func (a User) TableName() string {
	return "users"
}

// PublicServant represents the ATP metadata in the system for US policy makers
// Each PublicServant is associated with exactly one Actor via the Aid field.
type PublicServant struct {
	Base
	Aid       Aid           `db:"aid,omitempty"`
	Followers int64         `db:"followers,omitempty"`
	UserVotes int64         `db:"user_votes,omitempty"`
	PDS       sql.NullInt64 `db:"pds_id,omitempty"`
}

func (a PublicServant) TableName() string {
	return "public_servants"
}

// Legislator represents the legislator profile in the system
type Legislator struct {
	Base
	Aid          Aid           `db:"aid,omitempty,pk"        json:"aid"`
	DisplayName  string        `db:"display_name,omitempty"  json:"display_name"`
	LegislatorId int64         `db:"legislator_id,omitempty" json:"-"`
	PDS          sql.NullInt64 `db:"pds_id,omitempty"        json:"-"`
}

func (u Legislator) TableName() string {
	return "legislator"
}

// PolicyContent represents an item created by policy makers
type PolicyContent struct {
	Collection string `db:"collection"`
	Rkey       string `db:"rkey"`
	Cid        DbCID  `db:"cid"`
	Base
	AuthorID  Aid   `db:"author_id"`
	YayCount  int64 `db:"yay_count"`
	NayCount  int64 `db:"nay_count"`
	Followers uint  `db:"followers"`
	Deleted   bool  `db:"deleted"`
}

func (f PolicyContent) TableName() string {
	return "policy_content"
}

// Endorsement represents a like or endorsement of a post
type Endorsement struct {
	Created    string `db:"created"`
	Rkey       string `db:"rkey"`
	Cid        DbCID  `db:"cid"`
	EndorserID Aid    `db:"endorser_id"`
	ID         uint   `db:"id,omitempty,pk"`
	Post       uint   `db:"post_id"`
}

func (v Endorsement) TableName() string {
	return "endorsements"
}

// ActorFollow represents a follow relationship between actors
type ActorFollow struct {
	TargetCollection string `db:"target_collection"`
	Collection       string `db:"collection"`
	Rkey             string `db:"rkey"`
	Cid              DbCID  `db:"cid"`
	Metadata
	FollowerID Aid `db:"follower_id"`
	TargetID   Aid `db:"target_id"`
}

func (f ActorFollow) TableName() string {
	return "actor_follows"
}

// ContentFollow represents a follow relationship between an actor and content
type ContentFollow struct {
	Collection        string `db:"collection"`
	Rkey              string `db:"rkey"`
	SubjectCollection string `db:"subject_collection"`
	SubjectRkey       string `db:"subject_rkey"`
	Cid               DbCID  `db:"cid"`
	SubjectCid        DbCID  `db:"subject_cid"`
	Metadata
	FollowerID Aid `db:"follower_id"`
}

func (f ContentFollow) TableName() string {
	return "content_follows"
}

// ActorVote represents a follow relationship between actors
type ActorVote struct {
	VoteChoice VoteChoice `db:"vote_choice"`
	Metadata
	VoterID  Aid `db:"voter_id"`
	TargetID Aid `db:"target_id"`
}

func (f ActorVote) TableName() string {
	return "actor_votes"
}

// ContentVote represents a follow relationship between an actor and content
type ContentVote struct {
	VoteChoice        VoteChoice `db:"vote_choice"`
	SubjectCollection string     `db:"subject_collection"`
	Rkey              string     `db:"rkey"`
	Cid               DbCID      `db:"cid"`
	SubjectCid        DbCID      `db:"subject_cid"`
	Metadata
	FollowerID Aid `db:"follower_id"`
}

func (f ContentVote) TableName() string {
	return "content_votes"
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
//      Base
//      Domain string `db:"domain"`
// }
//
// func (d DomainBan) TableName() string {
//      return "domain_ban"
// }

// Feed represents a content feed with filtering criteria
type Feed struct {
	ID           uint      `db:"id,omitempty,pk"`
	IndexedAt    time.Time `db:"indexed_at,omitempty"`
	Rkey         string    `db:"rkey"`
	Cid          DbCID     `db:"cid"`
	Jurisdiction string    `db:"jurisdiction,omitempty"`
	Topic        []string  `db:"topic,omitempty"`
	Type         string    `db:"type"`
}

func (p Feed) TableName() string {
	return "feed"
}
