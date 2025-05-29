package keymgr

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"log"
	"log/slog"
	"time"

	"github.com/aws/aws-sdk-go-v2/service/kms"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	did "github.com/whyrusleeping/go-did"
)

// KeyCacher method signatures for working with the signing keys
type KeyCacher interface {
	Create(context.Context, string, any) ([]byte, error)
	Has(context.Context, string) bool
	Set(context.Context, string, []byte) error
	Sign(string, []byte) ([]byte, error)
	Remove(string) error
	Stop()
}

// KeyStore method signatures for working with the key store
type KeyStore interface {
	GetKey(context.Context, string) ([]byte, error)
	WriteNewKey(context.Context, string, []byte) error
}

// KeyManager contains all the dependencies for manager the key store and cache
type KeyManager struct {
	store         KeyStore
	repoKeyCacher KeyCacher
	plcKeyCacher  *plcKeyCache

	log *slog.Logger
}

// NewKeyManager initializes a 'KeyManager' struct
func NewKeyManager(
	ctx context.Context,
	kmsClient *kms.Client,
	s3Client *s3.Client,
	env, keyDir, recoveryKey string,
	eto time.Duration,
	sto time.Duration,
	logger *slog.Logger,
) (*KeyManager, error) {
	log.Println("Setting up key manager")

	if env == "local" {
		if _, err := s3Client.HeadBucket(ctx, &s3.HeadBucketInput{Bucket: &keyDir}); err != nil {
			log.Printf("The %s bucket does not exist, attempting to create bucket...\n", keyDir)
			if _, err := s3Client.CreateBucket(ctx, &s3.CreateBucketInput{Bucket: &keyDir}); err != nil {
				return nil, err
			}
			log.Println("Successfully created bucket!")
		}
	}

	rc := newRepoKeyCache(kmsClient, env, eto, sto)
	pc, err := newPLCKeyCache(ctx, kmsClient, env, recoveryKey)
	if err != nil {
		log.Printf("Failed to generated PLC rotation DID key: %v\n", err)
		return nil, err
	}

	log.Println("Successfully setup key manager!")

	return &KeyManager{
		store:         &s3KeyStore{client: s3Client, bucket: keyDir},
		repoKeyCacher: rc,
		plcKeyCacher:  pc,
		log:           logger.With("service", "keymgr"),
	}, nil
}

// CreateSigningKey generates the signing key for an actor
func (km *KeyManager) CreateSigningKey(ctx context.Context) (*did.PrivKey, error) {
	privkey, err := did.GeneratePrivKey(rand.Reader, did.KeyTypeSecp256k1)
	if err != nil {
		km.log.ErrorContext(ctx, "Failed to generate signing key", "error", err)
		return nil, err
	}

	return privkey, nil
}

// CreateEncryptedKey encrypts a signing key and writes it to the store
func (km *KeyManager) CreateEncryptedKey(ctx context.Context, did string, privkey *did.PrivKey) error {
	ek, err := km.repoKeyCacher.Create(ctx, did, privkey.Raw)
	if err != nil {
		km.log.ErrorContext(ctx, "Failed to encrypt signing key", "error", err, "did", did)
		return err
	}

	if err := km.store.WriteNewKey(ctx, did, ek); err != nil {
		km.log.ErrorContext(ctx, "Failed to write encrypted key to S3", "error", err, "did", did)
		return err
	}

	return nil
}

// CreateSystemApiKey generates the signing key for an actor
func (km *KeyManager) CreateSystemApiKey(ctx context.Context, did string) (string, error) {
	keyBytes := make([]byte, 32) // 256 bits
	if _, err := rand.Read(keyBytes); err != nil {
		return "", fmt.Errorf("failed to generate random key: %w", err)
	}
	apiKey := base64.URLEncoding.EncodeToString(keyBytes)

	// Save to SecretsManager here

	return apiKey, nil
}

// UpdateKeyCache updates the cache with both the signing and encrypted keys
func (km *KeyManager) UpdateKeyCache(ctx context.Context, did string) error {
	// Check the cache first to make sure we don't make unnecessary requests to S3
	if exists := km.repoKeyCacher.Has(ctx, did); !exists {
		ek, err := km.store.GetKey(ctx, did)
		if err != nil {
			km.log.ErrorContext(ctx, "Failed to read encrypted key from S3", "error", err, "did", did)
			return err
		}

		if err := km.repoKeyCacher.Set(ctx, did, ek); err != nil {
			km.log.ErrorContext(ctx, "Failed to update signing key cache", "error", err, "did", did)
			return err
		}
	}

	return nil
}

// InvalidateKeys removes signing and encrypted keys from the cache
func (km *KeyManager) InvalidateKeys(ctx context.Context, did string) {
	if err := km.repoKeyCacher.Remove(did); err != nil {
		km.log.WarnContext(ctx, "Failed to remove signing key from cache", "error", err, "did", did)
	}
}

// SignForActor checks for the signing key, refreshes the cache if the key isnt found, and finally signs the commit
func (km *KeyManager) SignForActor(ctx context.Context, did string, cmt []byte) ([]byte, error) {
	if err := km.UpdateKeyCache(ctx, did); err != nil {
		return nil, err
	}

	sig, err := km.repoKeyCacher.Sign(did, cmt)
	if err != nil {
		km.log.ErrorContext(ctx, "Failed to sign repo commit", "error", err, "did", did)
		return nil, err
	}

	return sig, nil
}

// RotationKey getter
func (km *KeyManager) RotationKey() string {
	return km.plcKeyCacher.plcRotationKey
}

// RecoveryKey getter
func (km *KeyManager) RecoveryKey() string {
	return km.plcKeyCacher.recoveryKey
}

// SignForPLC returns the signature for a signed PLC Op
func (km *KeyManager) SignForPLC(ctx context.Context, op []byte) ([]byte, error) {
	sig, err := km.plcKeyCacher.Sign(ctx, op)
	if err != nil {
		km.log.ErrorContext(ctx, "Failed to sign PLC operation", "error", err)
		return nil, err
	}

	return sig, nil
}

// VerifyActorSignature noop
func (km *KeyManager) VerifyActorSignature(ctx context.Context, did string, sig []byte, msg []byte) error {
	return fmt.Errorf("VerifyActorSignature not implemented")
}

func (km *KeyManager) Flush(ctx context.Context) error {
	done := make(chan struct{})

	go func() {
		km.repoKeyCacher.Stop()
		close(done)
	}()

	select {
	case <-done:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}
