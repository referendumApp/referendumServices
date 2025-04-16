package repo

import (
	"crypto/sha256"
	"encoding/base64"
	"fmt"
)

func LID(value1, value2, value3 string) string {
	combined := fmt.Sprintf("%s|%s|%s", value1, value2, value3)
	hash := sha256.Sum256([]byte(combined))
	return base64.RawURLEncoding.EncodeToString(hash[:10])
}
