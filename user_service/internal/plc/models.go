package plc

import (
	"context"
	"net/http"
	"time"

	"github.com/bluesky-social/indigo/plc"
	did "github.com/whyrusleeping/go-did"
)

type Client interface {
	plc.PLCClient
	GetOpAuditLog(ctx context.Context, did string) (*[]Op, error)
	TombstoneDID(ctx context.Context, sigkey *did.PrivKey, did string, prev string) error
}

type Server struct {
	C    *http.Client
	Host string
}

type Service struct {
	Type     string `json:"type" cborgen:"type"`
	Endpoint string `json:"endpoint" cborgen:"endpoint"`
}

type CreateOp struct {
	Prev                *string            `json:"prev" cborgen:"prev"`
	Type                string             `json:"type" cborgen:"type"`
	Sig                 string             `json:"sig" cborgen:"sig,omitempty"`
	Services            map[string]Service `json:"services" cborgen:"services"`
	VerificationMethods map[string]string  `json:"verificationMethods" cborgen:"verificationMethods"`
	AlsoKnownAs         []string           `json:"alsoKnownAs" cborgen:"alsoKnownAs"`
	RotationKeys        []string           `json:"rotationKeys" cborgen:"rotationKeys"`
}

type TombstoneOp struct {
	Prev string `json:"prev" cborgen:"prev"`
	Type string `json:"type" cborgen:"type"`
	Sig  string `json:"sig" cborgen:"sig,omitempty"`
}

type Op struct {
	DID       did.DID   `json:"did"`
	Operation CreateOp  `json:"operation"`
	CID       string    `json:"cid"`
	Nullified bool      `json:"nullfied"`
	CreatedAt time.Time `json:"createdAt"`
}
