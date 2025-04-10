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
	// otel "go.opentelemetry.io/otel"
)

type Server struct {
	C    *http.Client
	Host string
}

func (s Server) GetDocument(ctx context.Context, didstr string) (*did.Document, error) {
	// ctx, span := otel.Tracer("gosky").Start(ctx, "plsResolveDid")
	// defer span.End()

	if s.C == nil {
		s.C = http.DefaultClient
	}

	req, err := http.NewRequest("GET", s.Host+"/"+didstr, nil)
	if err != nil {
		return nil, err
	}

	resp, err := s.C.Do(req.WithContext(ctx))
	if err != nil {
		return nil, err
	}

	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("get did request failed (code %d): %s", resp.StatusCode, resp.Status)
	}

	var doc did.Document
	if err := json.NewDecoder(resp.Body).Decode(&doc); err != nil {
		return nil, err
	}

	return &doc, nil
}

func (s Server) FlushCacheFor(did string) {}

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

func (s Server) CreateDID(ctx context.Context, sigkey *did.PrivKey, recovery string, handle string, service string) (string, error) {
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

	body, err := json.Marshal(op) // nolint:errchkjson
	if err != nil {
		return "", fmt.Errorf("failed to marshal operation: %w", err)
	}

	req, err := http.NewRequest("POST", s.Host+"/"+url.QueryEscape(opdid), bytes.NewReader(body))
	if err != nil {
		return "", err
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := s.C.Do(req)
	if err != nil {
		return "", err
	}

	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		b, _ := io.ReadAll(resp.Body)
		fmt.Println(string(b))
		return "", fmt.Errorf("bad response from create call: %d %s", resp.StatusCode, resp.Status)
	}

	return opdid, nil
}

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
