package atp

import (
	"database/sql"
	"encoding/json"
	"time"

	"github.com/bluesky-social/indigo/xrpc"
)

type Uid uint64

type Base struct {
	CreatedAt time.Time    `db:"created_at,omitempty" json:"-"`
	UpdatedAt time.Time    `db:"updated_at,omitempty" json:"-"`
	DeletedAt sql.NullTime `db:"deleted_at,omitempty" json:"-"`
	ID        uint         `db:"id,omitempty,pk" json:"id"`
}

type User struct {
	Email          sql.NullString `db:"email,omitempty" json:"email"`
	HashedPassword sql.NullString `db:"hashed_password,omitempty" json:"-"`
	Handle         sql.NullString `db:"handle,omitempty" json:"-"`
	RecoveryKey    string         `db:"recovery_key,omitempty" json:"-"`
	Did            string         `db:"did,omitempty" json:"-"`
	CreatedAt      time.Time      `db:"created_at,omitempty" json:"-"`
	UpdatedAt      time.Time      `db:"updated_at,omitempty" json:"-"`
	DeletedAt      sql.NullTime   `db:"deleted_at,omitempty" json:"-"`
	ID             Uid            `db:"id,omitempty,pk" json:"id"`
	PDS            sql.NullInt64  `db:"pds_id,omitempty" json:"-"`
}

func (u User) TableName() string {
	return "user"
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
	Rkey string `db:"rkey" json:"rkey"`
	Cid  DbCID  `db:"cid" json:"cid"`
	Base
	Author       Uid   `db:"author" json:"author"`
	Endorsements int64 `db:"endorsements" json:"endorsements"`
	ReplyCount   int64 `db:"reply_count"`
	ReplyTo      uint  `db:"reply_to"`
	Missing      bool  `db:"missing"`
	Deleted      bool  `db:"deleted"`
}

func (f ActivityPost) TableName() string {
	return "activity_post"
}

type Settings struct {
	Deleted bool `db:"deleted" json:"deleted"`
}

func (u Settings) Marshal() ([]byte, error) {
	return json.Marshal(u)
}

func (u *Settings) Unmarshal(data []byte) error {
	return json.Unmarshal(data, u)
}

type Person struct {
	Settings    *Settings      `db:"settings,omitempty" json:"-"`
	Handle      sql.NullString `db:"handle,omitempty"`
	DisplayName string         `db:"display_name,omitempty"`
	Did         string         `db:"did,omitempty"`
	Type        sql.NullString `db:"type,omitempty"`
	Base
	Uid         Uid           `db:"uid,omitempty"`
	Following   int64         `db:"following,omitempty"`
	Followers   int64         `db:"followers,omitempty"`
	Posts       int64         `db:"posts,omitempty"`
	PDS         sql.NullInt64 `db:"pds_id,omitempty"`
	ValidHandle bool          `db:"valid_handle,omitempty"`
}

func (a Person) TableName() string {
	return "person"
}

// func (ai *Person) ActorRef() *bsky.ActorDefs_ProfileViewBasic {
// 	return &bsky.ActorDefs_ProfileViewBasic{
// 		Did:         ai.Did,
// 		Handle:      ai.Handle.String,
// 		DisplayName: &ai.DisplayName,
// 	}
// }
//
// func (ai *Person) ActorView() *bsky.ActorDefs_ProfileView {
// 	return &bsky.ActorDefs_ProfileView{
// 		Did:         ai.Did,
// 		Handle:      ai.Handle.String,
// 		DisplayName: &ai.DisplayName,
// 	}
// }

type EndorsementRecord struct {
	Created string `db:"created"`
	Rkey    string `db:"rkey"`
	Cid     DbCID  `db:"cid"`
	Base
	Endorser Uid  `db:"endorser"`
	Post     uint `db:"post_id"`
}

func (v EndorsementRecord) TableName() string {
	return "endorsement_record"
}

type UserFollowRecord struct {
	Rkey string `db:"rkey"`
	Cid  DbCID  `db:"cid"`
	Base
	Follower Uid `db:"follower"`
	Target   Uid `db:"target"`
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
	ID           uint      `db:"id,omitempty,pk" json:"id"`
	IndexedAt    time.Time `db:"indexed_at,omitempty" json:"-"`
	Rkey         string    `db:"rkey" json:"rkey"`
	Cid          DbCID     `db:"cid" json:"cid"`
	Jurisdiction string    `db:"jurisdiction,omitempty" json:"jurisdiction"`
	Topic        []string  `db:"topic,omitempty" json:"topic"`
	Type         string    `db:"type" json:"type"`
}

func (p Feed) TableName() string {
	return "feed"
}
