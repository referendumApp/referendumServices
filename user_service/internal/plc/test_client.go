package plc

import (
	"bytes"
	"context"
	"encoding/base64"
	"fmt"
	"sync"
	"time"

	cid "github.com/ipfs/go-cid"
	mh "github.com/multiformats/go-multihash"
	"github.com/referendumApp/referendumServices/internal/keymgr"
	cbg "github.com/whyrusleeping/cbor-gen"
	godid "github.com/whyrusleeping/go-did"
)

// TestClient contains test dependencies
type TestClient struct {
	km     *keymgr.KeyManager
	didDoc map[string]*godid.Document
	opLog  map[string][]LogOp
	lk     sync.RWMutex
}

// NewTestClient initializes a 'TestClient' struct
func NewTestClient(km *keymgr.KeyManager) *TestClient {
	return &TestClient{km: km, didDoc: make(map[string]*godid.Document), opLog: make(map[string][]LogOp)}
}

// GetDocument returns DID document
func (c *TestClient) GetDocument(ctx context.Context, didstr string) (*godid.Document, error) {
	c.lk.RLock()
	defer c.lk.RUnlock()

	return c.didDoc[didstr], nil
}

// FlushCacheFor noop
func (c *TestClient) FlushCacheFor(did string) {}

// CreateDID plc_operation for creating and returning a DID
func (c *TestClient) CreateDID(
	ctx context.Context,
	sigkey *godid.PrivKey,
	rotation []string,
	handle string,
	service string,
) (string, error) {
	op := &Op{
		Type:                "plc_operation",
		Services:            map[string]Service{"atproto_pds": {Type: "AtprotoPersonalDataClient", Endpoint: service}},
		AlsoKnownAs:         []string{handle},
		RotationKeys:        rotation,
		VerificationMethods: map[string]string{"atproto": sigkey.Public().DID()},
	}

	buf := new(bytes.Buffer)
	if err := op.MarshalCBOR(buf); err != nil {
		return "", err
	}

	sig, err := c.km.SignForPLC(ctx, buf.Bytes())
	if err != nil {
		return "", err
	}

	op.Sig = base64.RawURLEncoding.EncodeToString(sig)

	opdid, err := didForCreateOp(op)
	if err != nil {
		return "", err
	}

	c.lk.Lock()
	defer c.lk.Unlock()

	opCid, err := generateCid(op)
	if err != nil {
		return "", err
	}

	didObj, err := godid.ParseDID(opdid)
	if err != nil {
		return "", err
	}
	c.opLog[opdid] = []LogOp{
		{
			DID:       didObj,
			Operation: op,
			CID:       opCid.String(),
			Nullified: false,
			CreatedAt: time.Now(),
		},
	}

	return opdid, nil
}

// UpdateUserHandle noop
func (c *TestClient) UpdateUserHandle(ctx context.Context, did string, handle string) error {
	return fmt.Errorf("handle updates not yet implemented")
}

// GetOpAuditLog returns all PLC directory operations
func (c *TestClient) GetOpAuditLog(ctx context.Context, did string) ([]LogOp, error) {
	c.lk.RLock()
	defer c.lk.RUnlock()
	log := c.opLog[did]

	return log, nil
}

// TombstoneDID plc_operation for deleting/deactivating a DID
func (c *TestClient) TombstoneDID(ctx context.Context, did string, prev string) error {
	op := &TombstoneOp{Type: "plc_tombstone", Prev: prev}

	buf := new(bytes.Buffer)
	if err := op.MarshalCBOR(buf); err != nil {
		return err
	}

	sig, err := c.km.SignForPLC(ctx, buf.Bytes())
	if err != nil {
		return err
	}

	op.Sig = base64.RawURLEncoding.EncodeToString(sig)
	opCid, err := generateCid(op)
	if err != nil {
		return err
	}

	didObj, err := godid.ParseDID(did)
	if err != nil {
		return err
	}

	tombOp := LogOp{
		DID:       didObj,
		Operation: op,
		CID:       opCid.String(),
		Nullified: false,
		CreatedAt: time.Now(),
	}

	c.lk.Lock()
	defer c.lk.Unlock()
	opLog := c.opLog[did]
	c.opLog[did] = append(opLog, tombOp)
	delete(c.didDoc, did)

	return nil
}

// GetLatestOp wrapper around 'GetOpAuditLog' that returns the latest 'Op'
func (c *TestClient) GetLatestOp(ctx context.Context, did string) (*LogOp, error) {
	log, err := c.GetOpAuditLog(ctx, did)
	if err != nil {
		return nil, err
	}

	op, err := findLatestOp(log)
	if err != nil {
		return nil, err
	}

	return op, nil
}

func generateCid(op cbg.CBORMarshaler) (cid.Cid, error) {
	cidBuf := new(bytes.Buffer)
	if err := op.MarshalCBOR(cidBuf); err != nil {
		return cid.Undef, err
	}
	pref := cid.Prefix{
		Codec:    uint64(cid.DagCBOR),
		MhType:   mh.SHA2_256,
		MhLength: -1,
		Version:  1,
	}
	c, err := pref.Sum(cidBuf.Bytes())
	if err != nil {
		return cid.Undef, err
	}

	return c, nil
}
