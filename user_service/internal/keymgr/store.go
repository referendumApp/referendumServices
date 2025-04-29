package keymgr

import (
	"bytes"
	"context"
	"fmt"
	"io"

	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type s3KeyStore struct {
	client *s3.Client
	bucket string
}

func getKeyPath(did string) string {
	return fmt.Sprintf("%s.kms", did)
}

// GetKey S3 request to get encoded signing key
func (s *s3KeyStore) GetKey(ctx context.Context, did string) ([]byte, error) {
	path := getKeyPath(did)
	obj, err := s.client.GetObject(ctx, &s3.GetObjectInput{Bucket: &s.bucket, Key: &path})
	if err != nil {
		return nil, err
	}
	defer func() {
		_ = obj.Body.Close()
	}()

	body, err := io.ReadAll(obj.Body)
	if err != nil {
		return nil, err
	}

	return body, nil
}

// WriteNewKey S3 request to save encoded signing key
func (s *s3KeyStore) WriteNewKey(ctx context.Context, did string, key []byte) error {
	path := getKeyPath(did)
	contentType := "application/octet-stream"
	body := bytes.NewReader(key)
	if _, err := s.client.PutObject(ctx, &s3.PutObjectInput{Bucket: &s.bucket, Key: &path, Body: body, ContentType: &contentType}); err != nil {
		return err
	}

	return nil
}
