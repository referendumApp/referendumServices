package car

import (
	"bytes"
	"context"
	"fmt"
	"log"
	"os"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	"go.opentelemetry.io/otel"
)

type s3Client struct {
	client *s3.Client
	bucket string
}

func newS3Client(ctx context.Context, bucket string) (*s3Client, error) {
	awsCfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		log.Println("Failed to load configuration")
		return nil, err
	}
	client := s3.NewFromConfig(awsCfg, func(o *s3.Options) {
		endpoint := os.Getenv("S3_ENDPOINT_URL")
		if endpoint != "" {
			o.BaseEndpoint = &endpoint
		}
		o.UsePathStyle = true
		o.DisableLogOutputChecksumValidationSkipped = true
	})

	s3Client := &s3Client{client: client, bucket: bucket}

	if err := s3Client.storeExists(ctx); err != nil {
		log.Printf("The %s bucket does not exist, attempting to create bucket...", bucket)
		if _, err := client.CreateBucket(ctx, &s3.CreateBucketInput{Bucket: &bucket}); err != nil {
			return nil, err
		}
		log.Println("Successfully created bucket!")
	}

	return s3Client, nil
}

func (c *s3Client) storeExists(ctx context.Context) error {
	if _, err := c.client.HeadBucket(ctx, &s3.HeadBucketInput{Bucket: &c.bucket}); err != nil {
		return err
	}

	return nil
}

func (c *s3Client) writeNewShardFile(ctx context.Context, user atp.Uid, seq int, data []byte) (string, error) {
	_, span := otel.Tracer("carstore").Start(ctx, "writeNewShardFile")
	defer span.End()

	key := keyForShard(user, seq)
	contentType := "application/vnd.ipld.car"
	seekableReader := bytes.NewReader(data)
	if _, err := c.client.PutObject(ctx, &s3.PutObjectInput{Bucket: &c.bucket, Key: &key, Body: seekableReader, ContentType: &contentType}); err != nil {
		return "", err
	}
	// TODO: some overwrite protections
	// fname := filepath.Join(cs.dirForUser(user), fnameForShard(user, seq))
	// if err := os.WriteFile(fname, data, 0600); err != nil {
	// 	return "", err
	// }

	return key, nil
}

func (c *s3Client) readFile(ctx context.Context, key string, offset *int64) (*s3.GetObjectOutput, error) {
	var rng string
	if offset != nil {
		rng = fmt.Sprintf("bytes=%d-", *offset)
	}

	obj, err := c.client.GetObject(ctx, &s3.GetObjectInput{Bucket: &c.bucket, Key: &key, Range: &rng})
	if err != nil {
		return nil, fmt.Errorf("error getting car file: %w", err)
	}

	return obj, nil
}
