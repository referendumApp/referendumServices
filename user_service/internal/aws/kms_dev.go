package aws

import (
	"context"
	"log"
	"net/http"
	"net/url"

	"github.com/aws/aws-sdk-go-v2/service/kms"
	smithyendpoints "github.com/aws/smithy-go/endpoints"
)

type localKMSResolver struct {
	kmsHost string
}

// ResolveEndpoint the AWS KMS SDK method for re-directing requests
func (l *localKMSResolver) ResolveEndpoint(
	ctx context.Context,
	params kms.EndpointParameters,
) (smithyendpoints.Endpoint, error) {
	return smithyendpoints.Endpoint{URI: url.URL{Scheme: "http", Host: l.kmsHost, Path: "/"}}, nil
}

// Custom transport to intercept and modify KMS requests
type kmsTransport struct {
	base http.RoundTripper
}

// RoundTrip intercepts the KMS request to add logging and insert header deps
func (t *kmsTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	log.Printf("Making KMS request to: %s\n", req.URL.String())
	log.Printf("Request Target: %s\n", req.Header.Get("X-Amz-Target"))

	if req.Header.Get("Content-Type") == "" {
		req.Header.Set("Content-Type", "application/x-amz-json-1.1")
	}

	req.Header.Del("Authorization")

	// Make the request
	resp, err := t.base.RoundTrip(req)

	if err != nil {
		log.Printf("Request error: %v\n", err)
	}

	return resp, err
}
