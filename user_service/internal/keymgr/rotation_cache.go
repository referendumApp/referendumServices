package keymgr

import (
	"context"
	"encoding/asn1"
	"fmt"
	"log"
	"math/big"

	"github.com/aws/aws-sdk-go-v2/service/kms"
	"github.com/aws/aws-sdk-go-v2/service/kms/types"
	"github.com/whyrusleeping/go-did"
	secpEc "gitlab.com/yawning/secp256k1-voi/secec"
)

type plcKeyCache struct {
	kmsClient      *kms.Client
	kmsAlias       string
	plcRotationKey string
	recoveryKey    string
}

func newPLCKeyCache(
	ctx context.Context,
	kmsClient *kms.Client,
	env string,
	recoveryKey string,
) (*plcKeyCache, error) {
	rc := &plcKeyCache{
		kmsClient:   kmsClient,
		kmsAlias:    "alias/" + env + "-plc",
		recoveryKey: recoveryKey,
	}

	out, err := rc.kmsClient.GetPublicKey(ctx, &kms.GetPublicKeyInput{KeyId: &rc.kmsAlias})
	if err != nil {
		log.Println("Failed to get PLC rotation public key from KMS")
		return nil, err
	}
	pk, err := secpEc.ParseASN1PublicKey(out.PublicKey)
	if err != nil {
		log.Fatalf("Failed to parse KMS public key: %v", err)
		return nil, err
	}

	pub := did.PubKey{Raw: pk, Type: did.KeyTypeSecp256k1}

	rc.plcRotationKey = pub.DID()

	return rc, nil
}

// GetKeys returns a string slice of rotation keys in the cache
func (rc *plcKeyCache) GetKeys() []string {
	return []string{rc.recoveryKey, rc.plcRotationKey}
}

// Sign gets the signing key and returns the signature
func (rc *plcKeyCache) Sign(ctx context.Context, op []byte) ([]byte, error) {
	out, err := rc.kmsClient.Sign(
		ctx,
		&kms.SignInput{KeyId: &rc.kmsAlias, Message: op, SigningAlgorithm: types.SigningAlgorithmSpecEcdsaSha256},
	)
	if err != nil {
		return nil, err
	}

	return convertDERToCompact(out.Signature)
}

type ecdsaSignature struct {
	R, S *big.Int
}

func convertDERToCompact(derSignature []byte) ([]byte, error) {
	// Parse DER signature to extract R and S values
	var sig ecdsaSignature
	if _, err := asn1.Unmarshal(derSignature, &sig); err != nil {
		return nil, fmt.Errorf("failed to parse DER signature: %w", err)
	}

	// For secp256k1, each value is 32 bytes
	const fieldSize = 32

	// For secp256k1, the curve order N
	curveN, _ := new(big.Int).SetString("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)
	halfN := new(big.Int).Rsh(curveN, 1) // N/2

	// If S > N/2, set S = N - S (this ensures low-S values)
	if sig.S.Cmp(halfN) > 0 {
		sig.S = new(big.Int).Sub(curveN, sig.S)
	}

	// Create compact signature (R || S), padded to fieldSize
	compact := make([]byte, fieldSize*2)

	// Copy R with padding
	rBytes := sig.R.Bytes()
	if len(rBytes) > fieldSize {
		return nil, fmt.Errorf("signature R value too large: %d bytes", len(rBytes))
	}
	copy(compact[fieldSize-len(rBytes):fieldSize], rBytes)

	// Copy S with padding
	sBytes := sig.S.Bytes()
	if len(sBytes) > fieldSize {
		return nil, fmt.Errorf("signature S value too large: %d bytes", len(sBytes))
	}
	copy(compact[fieldSize*2-len(sBytes):], sBytes)

	return compact, nil
}
