package repo

import (
	"encoding/base32"
	"fmt"
	"strings"
)

func NextLID(value1, value2, value3 string) string {
	combined := fmt.Sprintf("%s|%s|%s", value1, value2, value3)

	encoded := base32.StdEncoding.EncodeToString([]byte(combined))

	return strings.TrimRight(encoded, "=")
}

func RetrieveValuesFromLID(key string) (string, string, string, error) {
	padding := len(key) % 8
	if padding > 0 {
		key += strings.Repeat("=", 8-padding)
	}

	decoded, err := base32.StdEncoding.DecodeString(key)
	if err != nil {
		return "", "", "", err
	}

	parts := strings.Split(string(decoded), "|")
	if len(parts) != 3 {
		return "", "", "", fmt.Errorf("invalid key format")
	}

	return parts[0], parts[1], parts[2], nil
}
