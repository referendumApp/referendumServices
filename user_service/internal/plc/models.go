package plc

import (
	"encoding/json"
	"time"

	cbg "github.com/whyrusleeping/cbor-gen"
	did "github.com/whyrusleeping/go-did"
)

// Service schema for the Services field in a DID document
type Service struct {
	Type     string `json:"type"     cborgen:"type"`
	Endpoint string `json:"endpoint" cborgen:"endpoint"`
}

// Op PLC operation schema
type Op struct {
	Prev                *string            `json:"prev"                cborgen:"prev"`
	Type                string             `json:"type"                cborgen:"type"`
	Sig                 string             `json:"sig"                 cborgen:"sig,omitempty"`
	Services            map[string]Service `json:"services"            cborgen:"services"`
	VerificationMethods map[string]string  `json:"verificationMethods" cborgen:"verificationMethods"`
	AlsoKnownAs         []string           `json:"alsoKnownAs"         cborgen:"alsoKnownAs"`
	RotationKeys        []string           `json:"rotationKeys"        cborgen:"rotationKeys"`
}

// TombstoneOp PLC operation schema for tombstoning a DID
type TombstoneOp struct {
	Prev string `json:"prev" cborgen:"prev"`
	Type string `json:"type" cborgen:"type"`
	Sig  string `json:"sig"  cborgen:"sig,omitempty"`
}

type Operation interface {
	cbg.CBORMarshaler
	cbg.CBORUnmarshaler
}

// LogOp response schema from PLC server
type LogOp struct {
	DID       did.DID   `json:"did"`
	Operation Operation `json:"operation"`
	CID       string    `json:"cid"`
	Nullified bool      `json:"nullfied"`
	CreatedAt time.Time `json:"createdAt"`
}

func (l *LogOp) UnmarshalJSON(data []byte) error {
	type TempLogOp struct {
		DID       did.DID   `json:"did"`
		Operation *Op       `json:"operation"`
		CID       string    `json:"cid"`
		Nullified bool      `json:"nullified"`
		CreatedAt time.Time `json:"createdAt"`
	}

	var temp TempLogOp
	if err := json.Unmarshal(data, &temp); err != nil {
		return err
	}

	l.DID = temp.DID
	l.Operation = temp.Operation
	l.CID = temp.CID
	l.Nullified = temp.Nullified
	l.CreatedAt = temp.CreatedAt

	return nil
}
