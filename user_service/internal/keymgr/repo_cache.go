package keymgr

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/awnumar/memguard"
	"github.com/aws/aws-sdk-go-v2/service/kms"
	godid "github.com/whyrusleeping/go-did"
	secpEc "gitlab.com/yawning/secp256k1-voi/secec"
)

type encryptKeyCache struct {
	cache          map[string]*encryptKey
	sessionTimeout time.Duration
}

type encryptKey struct {
	value     []byte
	expiresAt time.Time
}

func (ec *encryptKeyCache) add(did string, ek []byte) {
	ec.cache[did] = &encryptKey{value: ek, expiresAt: time.Now().Add(ec.sessionTimeout)}
}

type signKeyCache struct {
	cache          map[string]*signKey
	sessionTimeout time.Duration
}

type signKey struct {
	value     *godid.PrivKey
	expiresAt time.Time
}

func (sc *signKeyCache) add(did string, secureBuf *memguard.LockedBuffer) error {
	raw, err := secpEc.NewPrivateKey(secureBuf.Bytes())
	if err != nil {
		return fmt.Errorf("error decoding signing key: %w", err)
	}
	sc.cache[did] = &signKey{
		value:     &godid.PrivKey{Raw: raw, Type: godid.KeyTypeSecp256k1},
		expiresAt: time.Now().Add(sc.sessionTimeout),
	}

	return nil
}

type repoKeyCache struct {
	kmsClient       *kms.Client
	kmsAlias        string
	encryptKeyCache *encryptKeyCache
	signKeyCache    *signKeyCache
	mu              sync.RWMutex
}

func newRepoKeyCache(kmsClient *kms.Client, env string, eto time.Duration, sto time.Duration) *repoKeyCache {
	kc := &repoKeyCache{
		kmsClient:       kmsClient,
		kmsAlias:        "alias/" + env + "-did-master",
		encryptKeyCache: &encryptKeyCache{cache: make(map[string]*encryptKey), sessionTimeout: eto},
		signKeyCache:    &signKeyCache{cache: make(map[string]*signKey), sessionTimeout: sto},
	}

	go kc.cleanupExpiredKeys()

	return kc
}

// Create encrypts the signing key and returns the encrypted key
func (kc *repoKeyCache) Create(ctx context.Context, did string, sk any) ([]byte, error) {
	pt, ok := sk.(*secpEc.PrivateKey)
	if !ok {
		return nil, fmt.Errorf("invalid secp256k1 privatey key")
	}

	out, err := kc.kmsClient.Encrypt(
		ctx,
		&kms.EncryptInput{
			KeyId:             &kc.kmsAlias,
			Plaintext:         pt.Bytes(),
			EncryptionContext: map[string]string{"did": did},
		},
	)
	if err != nil {
		return nil, fmt.Errorf("error creating encrypted key: %w", err)
	}

	return out.CiphertextBlob, nil
}

// Has checks signing key cache first, if its expired then attempts to refresh the cache if the encrypted key isn't expired
func (kc *repoKeyCache) Has(ctx context.Context, did string) bool {
	kc.mu.RLock()
	skExists := kc.signKeyCache.cache[did] != nil
	ek, ekExists := kc.encryptKeyCache.cache[did]
	kc.mu.RUnlock()

	if skExists {
		return true
	}

	if ekExists {
		if err := kc.Set(ctx, did, ek.value); err != nil {
			return false
		}
		return true
	}

	return false
}

// Set decrypts a KMS encrypted key and updates both caches
func (kc *repoKeyCache) Set(ctx context.Context, did string, key []byte) error {
	out, err := kc.kmsClient.Decrypt(
		ctx,
		&kms.DecryptInput{
			CiphertextBlob:    key,
			EncryptionContext: map[string]string{"did": did},
		},
	)
	if err != nil {
		return fmt.Errorf("kms decrypt request failed: %w", err)
	}

	secureBuf := memguard.NewBufferFromBytes(out.Plaintext)
	defer secureBuf.Destroy()

	kc.mu.Lock()
	defer kc.mu.Unlock()

	kc.encryptKeyCache.add(did, key)
	if err := kc.signKeyCache.add(did, secureBuf); err != nil {
		return err
	}

	return nil
}

// Remove removes signing and encrypted keys from the cache
func (kc *repoKeyCache) Remove(did string) {
	kc.mu.Lock()
	delete(kc.encryptKeyCache.cache, did)
	delete(kc.signKeyCache.cache, did)
	kc.mu.Unlock()
}

// Sign gets the signing key and returns the signature
func (kc *repoKeyCache) Sign(did string, cmt []byte) ([]byte, error) {
	kc.mu.RLock()
	defer kc.mu.RUnlock()

	sk, exists := kc.signKeyCache.cache[did]
	if !exists {
		return nil, fmt.Errorf("key manager does not have a signing key, cannot sign")
	}
	return sk.value.Sign(cmt)
}

func (kc *repoKeyCache) cleanupExpiredKeys() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		kc.mu.Lock()
		now := time.Now()

		for did, ek := range kc.encryptKeyCache.cache {
			if now.After(ek.expiresAt) {
				delete(kc.encryptKeyCache.cache, did)
				delete(kc.signKeyCache.cache, did)
			}
		}

		for did, sk := range kc.signKeyCache.cache {
			if now.After(sk.expiresAt) {
				delete(kc.signKeyCache.cache, did)
			}
		}

		kc.mu.Unlock()
	}
}
