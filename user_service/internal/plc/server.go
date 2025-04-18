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
	"net/http"
	"net/url"
	"strings"

	did "github.com/whyrusleeping/go-did"
	otel "go.opentelemetry.io/otel"
)

// GetDocument returns DID document
func (s Server) GetDocument(ctx context.Context, didstr string) (*did.Document, error) {
	ctx, span := otel.Tracer("gosky").Start(ctx, "plsResolveDid")
	defer span.End()

	if s.C == nil {
		s.C = http.DefaultClient
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, s.Host+"/"+didstr, nil)
	if err != nil {
		return nil, err
	}

	resp, err := s.C.Do(req.WithContext(ctx))
	if err != nil {
		return nil, err
	}

	defer func() {
		if err := resp.Body.Close(); err != nil {
			s.log.ErrorContext(ctx, "Error closing response body", "error", err)
		}
	}()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		s.log.InfoContext(ctx, "DID doc request to plc directory failed", "body", string(b))
		return nil, fmt.Errorf("get did request failed (code %d): %s", resp.StatusCode, resp.Status)
	}

	var doc did.Document
	if err := json.NewDecoder(resp.Body).Decode(&doc); err != nil {
		return nil, err
	}

	return &doc, nil
}

// FlushCacheFor noop
func (s Server) FlushCacheFor(did string) {}

// CreateDID plc_operation for creating and returning a DID
func (s Server) CreateDID(
	ctx context.Context,
	sigkey *did.PrivKey,
	recovery string,
	handle string,
	service string,
) (string, error) {
	if s.C == nil {
		s.C = http.DefaultClient
	}

	op := CreateOp{
		Type:                "plc_operation",
		Services:            map[string]Service{"atproto_pds": {Type: "AtprotoPersonalDataServer", Endpoint: service}},
		AlsoKnownAs:         []string{handle},
		RotationKeys:        []string{recovery},
		VerificationMethods: map[string]string{"atproto": sigkey.Public().DID()},
	}

	buf := new(bytes.Buffer)
	if err := op.MarshalCBOR(buf); err != nil {
		return "", err
	}

	sig, err := sigkey.Sign(buf.Bytes())
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
		s.Host+"/"+url.QueryEscape(opdid),
		bytes.NewReader(body),
	)
	if err != nil {
		return "", err
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := s.C.Do(req)
	if err != nil {
		return "", err
	}

	defer func() {
		if err := resp.Body.Close(); err != nil {
			s.log.ErrorContext(ctx, "Error closing response body", "error", err)
		}
	}()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		s.log.InfoContext(ctx, "Create PLC operation request failed", "body", string(b))
		return "", fmt.Errorf("bad response from create call: %d %s", resp.StatusCode, resp.Status)
	}

	return opdid, nil
}

// UpdateUserHandle not implemented
func (s Server) UpdateUserHandle(ctx context.Context, did string, handle string) error {
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
func (s Server) GetOpAuditLog(ctx context.Context, did string) (*[]Op, error) {
	if s.C == nil {
		s.C = http.DefaultClient
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, s.Host+"/"+url.QueryEscape(did)+"/log/audit", nil)
	if err != nil {
		return nil, err
	}

	resp, err := s.C.Do(req.WithContext(ctx))
	if err != nil {
		return nil, err
	}

	defer func() {
		if err := resp.Body.Close(); err != nil {
			s.log.ErrorContext(ctx, "Error closing response body", "error", err)
		}
	}()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		s.log.InfoContext(ctx, "Audit log request to plc directory failed", "body", string(b))
		return nil, fmt.Errorf("get last op request failed (code %d): %s", resp.StatusCode, resp.Status)
	}

	var log []Op
	if err := json.NewDecoder(resp.Body).Decode(&log); err != nil {
		return nil, err
	}

	return &log, nil
}

// TombstoneDID plc_operation for deleting/deactivating a DID
func (s Server) TombstoneDID(ctx context.Context, sigkey *did.PrivKey, did string, prev string) error {
	if s.C == nil {
		s.C = http.DefaultClient
	}

	op := TombstoneOp{Type: "plc_tombstone", Prev: prev}

	buf := new(bytes.Buffer)
	if err := op.MarshalCBOR(buf); err != nil {
		return err
	}

	sig, err := sigkey.Sign(buf.Bytes())
	if err != nil {
		return err
	}

	op.Sig = base64.RawURLEncoding.EncodeToString(sig)

	body, err := json.Marshal(op) //nolint:errchkjson
	if err != nil {
		return fmt.Errorf("failed to marshal operation: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, s.Host+"/"+url.QueryEscape(did), bytes.NewReader(body))
	if err != nil {
		return err
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := s.C.Do(req.WithContext(ctx))
	if err != nil {
		return err
	}

	defer func() {
		if err := resp.Body.Close(); err != nil {
			s.log.ErrorContext(ctx, "Error closing response body", "error", err)
		}
	}()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		s.log.InfoContext(ctx, "Tombstone request to plc directory failed", "body", string(b))
		return fmt.Errorf("bad response from tombstone call: %d %s", resp.StatusCode, resp.Status)
	}

	return nil
}

// GetLatestOp wrapper around 'GetOpAuditLog' that returns the latest 'Op'
func (s Server) GetLatestOp(ctx context.Context, did string) (*Op, error) {
	log, err := s.GetOpAuditLog(ctx, did)
	if err != nil {
		return nil, err
	}

	op, err := findLatestOp(log)
	if err != nil {
		return nil, err
	}

	return op, nil
}
