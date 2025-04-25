package util

import (
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"math"
	"strings"

	"golang.org/x/crypto/argon2"
)

// Argon2Params defines parameters for the Argon2id algorithm
type Argon2Params struct {
	Memory      uint32
	Iterations  uint32
	Parallelism uint8
	SaltLength  uint32
	KeyLength   uint32
}

// DefaultParams provides recommended default parameters
func DefaultParams() *Argon2Params {
	return &Argon2Params{
		Memory:      64 * 1024, // 64MB
		Iterations:  3,
		Parallelism: 4,
		SaltLength:  16,
		KeyLength:   32,
	}
}

// HashPassword creates an Argon2id hash from a plain password
func HashPassword(password string, params *Argon2Params) (string, error) {
	// Generate a random salt
	salt := make([]byte, params.SaltLength)
	if _, err := rand.Read(salt); err != nil {
		return "", err
	}

	// Hash the password
	hash := argon2.IDKey(
		[]byte(password),
		salt,
		params.Iterations,
		params.Memory,
		params.Parallelism,
		params.KeyLength,
	)

	// Encode as "argon2id$v=19$m=65536,t=3,p=2$<salt>$<hash>"
	b64Salt := base64.RawStdEncoding.EncodeToString(salt)
	b64Hash := base64.RawStdEncoding.EncodeToString(hash)

	encodedHash := fmt.Sprintf(
		"$argon2id$v=19$m=%d,t=%d,p=%d$%s$%s",
		params.Memory,
		params.Iterations,
		params.Parallelism,
		b64Salt,
		b64Hash,
	)

	return encodedHash, nil
}

// VerifyPassword checks if a password matches a hash
func VerifyPassword(password, encodedHash string) (bool, error) {
	// Extract parts from the hash
	parts := strings.Split(encodedHash, "$")
	if len(parts) != 6 {
		return false, fmt.Errorf("invalid hash format")
	}

	// Parse the parameters
	var params Argon2Params
	_, err := fmt.Sscanf(parts[3], "m=%d,t=%d,p=%d", &params.Memory, &params.Iterations, &params.Parallelism)
	if err != nil {
		return false, err
	}

	// Decode the salt and hash
	salt, err := base64.RawStdEncoding.DecodeString(parts[4])
	if err != nil {
		return false, err
	}

	decodedHash, err := base64.RawStdEncoding.DecodeString(parts[5])
	if err != nil {
		return false, err
	}
	hashLen := len(decodedHash)
	if hashLen > math.MaxUint32 {
		return false, fmt.Errorf("decoded hash length exceeds maximum allowed")
	}
	params.KeyLength = uint32(hashLen)

	// Hash the password with the same parameters and salt
	hash := argon2.IDKey(
		[]byte(password),
		salt,
		params.Iterations,
		params.Memory,
		params.Parallelism,
		params.KeyLength,
	)

	// Compare the computed hash with the stored hash
	return compareHashAndPassword(hash, decodedHash), nil
}

// compareHashAndPassword compares a hash with a password in constant time
func compareHashAndPassword(a, b []byte) bool {
	if len(a) != len(b) {
		return false
	}

	// bitwise OR operation to ensure that all bytes match between the two slices
	var equal = byte(0)
	for i := range a {
		equal |= a[i] ^ b[i]
	}

	return equal == 0
}
