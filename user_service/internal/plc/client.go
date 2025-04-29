package plc

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/base32"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"strings"

	didres "github.com/bluesky-social/indigo/did"
	"github.com/referendumApp/referendumServices/internal/keymgr"
	did "github.com/whyrusleeping/go-did"
	otel "go.opentelemetry.io/otel"
)

// ServiceClient method implementations for PLC server endpoints and operations
type ServiceClient interface {
	didres.Resolver
	CreateDID(
		ctx context.Context,
		sigkey *did.PrivKey,
		rotation []string,
		handle string,
		service string,
	) (string, error)
	UpdateUserHandle(ctx context.Context, didstr string, nhandle string) error
	GetOpAuditLog(ctx context.Context, did string) (*[]Op, error)
	GetLatestOp(ctx context.Context, did string) (*Op, error)
	TombstoneDID(ctx context.Context, did string, prev string) error
}

// Client contains the host and client for making PLC directory requests
type Client struct {
	C    *http.Client
	Host string
	km   *keymgr.KeyManager
	log  *slog.Logger
}

// NewPLCClient initializes a 'Client' struct
func NewPLCClient(host string, km *keymgr.KeyManager, logger *slog.Logger) *Client {
	return &Client{Host: host, C: http.DefaultClient, km: km, log: logger.With("service", "plc")}
}

// GetDocument returns DID document
func (c Client) GetDocument(ctx context.Context, didstr string) (*did.Document, error) {
	ctx, span := otel.Tracer("plc").Start(ctx, "plsResolveDid")
	defer span.End()

	if c.C == nil {
		c.C = http.DefaultClient
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.Host+"/"+didstr, nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.C.Do(req.WithContext(ctx))
	if err != nil {
		return nil, err
	}

	defer func() {
		if err := resp.Body.Close(); err != nil {
			c.log.ErrorContext(ctx, "Error closing response body", "error", err)
		}
	}()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		c.log.InfoContext(ctx, "DID doc request to plc directory failed", "body", string(b))
		return nil, fmt.Errorf("get did request failed (code %d): %s", resp.StatusCode, resp.Status)
	}

	var doc did.Document
	if err := json.NewDecoder(resp.Body).Decode(&doc); err != nil {
		return nil, err
	}

	return &doc, nil
}

// FlushCacheFor noop
func (c Client) FlushCacheFor(did string) {}

// CreateDID plc_operation for creating and returning a DID
func (c Client) CreateDID(
	ctx context.Context,
	sigkey *did.PrivKey,
	rotation []string,
	handle string,
	service string,
) (string, error) {
	if c.C == nil {
		c.C = http.DefaultClient
	}

	op := CreateOp{
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

	opdid, err := didForCreateOp(&op)
	if err != nil {
		return "", err
	}

	body, err := json.Marshal(op) //nolint:errchkjson
	if err != nil {
		return "", fmt.Errorf("failed to marshal operation: %w", err)
	}

	req, err := http.NewRequestWithContext(
		ctx,
		http.MethodPost,
		c.Host+"/"+url.QueryEscape(opdid),
		bytes.NewReader(body),
	)
	if err != nil {
		return "", err
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := c.C.Do(req)
	if err != nil {
		return "", err
	}

	defer func() {
		if err := resp.Body.Close(); err != nil {
			c.log.ErrorContext(ctx, "Error closing response body", "error", err)
		}
	}()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		c.log.InfoContext(ctx, "Create PLC operation request failed", "body", string(b))
		return "", fmt.Errorf("bad response from create call: %d %s", resp.StatusCode, resp.Status)
	}

	return opdid, nil
}

// UpdateUserHandle not implemented
func (c Client) UpdateUserHandle(ctx context.Context, did string, handle string) error {
	return fmt.Errorf("handle updates not yet implemented")
}

func didForCreateOp(op *CreateOp) (string, error) {
	buf := new(bytes.Buffer)
	if err := op.MarshalCBOR(buf); err != nil {
		return "", err
	}

	h := sha256.Sum256(buf.Bytes())
	enchash := base32.StdEncoding.EncodeToString(h[:])
	enchash = strings.ToLower(enchash)
	return "did:plc:" + enchash[:24], nil
}

// GetOpAuditLog returns all PLC directory operations
func (c Client) GetOpAuditLog(ctx context.Context, did string) (*[]Op, error) {
	if c.C == nil {
		c.C = http.DefaultClient
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.Host+"/"+url.QueryEscape(did)+"/log/audit", nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.C.Do(req.WithContext(ctx))
	if err != nil {
		return nil, err
	}

	defer func() {
		if err := resp.Body.Close(); err != nil {
			c.log.ErrorContext(ctx, "Error closing response body", "error", err)
		}
	}()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		c.log.InfoContext(ctx, "Audit log request to plc directory failed", "body", string(b))
		return nil, fmt.Errorf("get last op request failed (code %d): %s", resp.StatusCode, resp.Status)
	}

	var log []Op
	if err := json.NewDecoder(resp.Body).Decode(&log); err != nil {
		return nil, err
	}

	return &log, nil
}

// TombstoneDID plc_operation for deleting/deactivating a DID
func (c Client) TombstoneDID(ctx context.Context, did string, prev string) error {
	if c.C == nil {
		c.C = http.DefaultClient
	}

	op := TombstoneOp{Type: "plc_tombstone", Prev: prev}

	buf := new(bytes.Buffer)
	if err := op.MarshalCBOR(buf); err != nil {
		return err
	}

	sig, err := c.km.SignForPLC(ctx, buf.Bytes())
	if err != nil {
		return err
	}

	op.Sig = base64.RawURLEncoding.EncodeToString(sig)

	body, err := json.Marshal(op) //nolint:errchkjson
	if err != nil {
		c.log.InfoContext(ctx, "Failed to marshal tombstone operation", "error", err)
		return err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.Host+"/"+url.QueryEscape(did), bytes.NewReader(body))
	if err != nil {
		return err
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := c.C.Do(req.WithContext(ctx))
	if err != nil {
		return err
	}

	defer func() {
		if err := resp.Body.Close(); err != nil {
			c.log.ErrorContext(ctx, "Error closing response body", "error", err)
		}
	}()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		c.log.InfoContext(ctx, "Tombstone request to plc directory failed", "body", string(b))
		return fmt.Errorf("bad response from tombstone call: %d %s", resp.StatusCode, resp.Status)
	}

	return nil
}

// GetLatestOp wrapper around 'GetOpAuditLog' that returns the latest 'Op'
func (c Client) GetLatestOp(ctx context.Context, did string) (*Op, error) {
	log, err := c.GetOpAuditLog(ctx, did)
	if err != nil {
		return nil, err
	}

	op, err := findLatestOp(log)
	if err != nil {
		c.log.InfoContext(ctx, "Failed to get the latest PLC operation", "err", err)
		return nil, err
	}

	return op, nil
}
