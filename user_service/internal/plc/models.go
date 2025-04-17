package plc

import (
	"context"
	"fmt"
	"log/slog"
	"net/http"
	"time"

	"github.com/bluesky-social/indigo/plc"
	did "github.com/whyrusleeping/go-did"
)

type Client interface {
	plc.PLCClient
	GetOpAuditLog(ctx context.Context, did string) (*[]Op, error)
	GetLatestOp(ctx context.Context, did string) (*Op, error)
	TombstoneDID(ctx context.Context, sigkey *did.PrivKey, did string, prev string) error
}

type Server struct {
	C    *http.Client
	Host string
	log  *slog.Logger
}

func NewPLCServer(host string) *Server {
	return &Server{Host: host, C: http.DefaultClient, log: slog.Default().With("system", "plc")}
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

func findLatestOp(log *[]Op) (*Op, error) {
	derefLog := *log

	if len(derefLog) == 0 {
		return nil, fmt.Errorf("no operations found in PLC log")
	}

	newest := &derefLog[0]

	for _, op := range derefLog[1:] {
		if op.CreatedAt.After(newest.CreatedAt) {
			newest = &op
		}
	}

	return newest, nil
}
