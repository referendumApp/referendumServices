package aws

import (
	"context"
	"log"
	"net/http"
	"os"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/kms"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/secretsmanager"
)

// Clients holds all AWS service clients
type Clients struct {
	S3             *s3.Client
	SECRETSMANAGER *secretsmanager.Client
	KMS            *kms.Client
}

// NewClients creates and initializes all AWS clients
func NewClients(ctx context.Context, env string) (*Clients, error) {
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return nil, err
	}

	s3Client := s3.NewFromConfig(cfg, func(o *s3.Options) {
		endpoint := os.Getenv("S3_ENDPOINT_URL")
		if endpoint != "" {
			o.BaseEndpoint = &endpoint
		}
		o.UsePathStyle = true
		o.DisableLogOutputChecksumValidationSkipped = true
	})

	secretsmanagerClient := secretsmanager.NewFromConfig(cfg, func(o *secretsmanager.Options) {
		endpoint := os.Getenv("SECRETS_MANAGER_ENDPOINT_URL")
		if endpoint != "" {
			o.BaseEndpoint = &endpoint
		}
	})

	kmsClient := kms.NewFromConfig(cfg, func(o *kms.Options) {
		if env == "local" {
			log.Println("Configuring local KMS client")
			o.EndpointResolverV2 = &localKMSResolver{kmsHost: os.Getenv("KMS_HOST")}
			o.HTTPClient = &http.Client{Transport: &kmsTransport{base: http.DefaultTransport}}
		}
	})

	return &Clients{

		S3:             s3Client,
		SECRETSMANAGER: secretsmanagerClient,
		KMS:            kmsClient,
	}, nil
}
