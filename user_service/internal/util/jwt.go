package util

import (
	"errors"
	"fmt"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
)

// ContextKeyType type alias map claim keys
type ContextKeyType string

// map claim keys types
const (
	SubjectKey ContextKeyType = "aid"
	DidKey     ContextKeyType = "did"
)

// TokenType type alias for access and refresh token types
type TokenType string

// Auth token types
const (
	Access  TokenType = "access"
	Refresh TokenType = "refresh"
)

// Token expiry times
const (
	AccessExpiry  = 30 * time.Minute
	RefreshExpiry = 24 * time.Hour
)

// Auth Constants
const (
	DefaultHeaderAuthorization = "Authorization"
	DefaultAuthScheme          = "Bearer"
)

// JWTConfig contains all the metadata for validating and creating JWT tokens
type JWTConfig struct {
	// Signing key to validate token.
	// This is one of the three options to provide a token validation key.
	// The order of precedence is a user-defined KeyFunc, SigningKeys and SigningKey.
	// Required if neither user-defined KeyFunc nor SigningKeys is provided.
	SigningKey any

	// Signing method used to check the token's signing algorithm.
	// Optional. Default value HS256.
	SigningMethod *jwt.SigningMethodHMAC

	Issuer string

	// Context key to store user information from the token into context.
	// Optional. Default value "user".
	SubjectKey ContextKeyType

	DidKey ContextKeyType

	// TokenLookup is a string in the form of "<source>:<name>" or "<source>:<name>,<source>:<name>" that is used
	// to extract token from the request.
	// Optional. Default value "header:Authorization".
	// Possible values:
	// - "header:<name>" or "header:<name>:<cut-prefix>"
	// 			`<cut-prefix>` is argument value to cut/trim prefix of the extracted value. This is useful if header
	//			value has static prefix like `Authorization: <auth-scheme> <authorisation-parameters>` where part that we
	//			want to cut is `<auth-scheme> ` note the space at the end.
	//			In case of JWT tokens `Authorization: Bearer <token>` prefix we cut is `Bearer `.
	// If prefix is left empty the whole value is returned.
	// - "query:<name>"
	// - "param:<name>"
	// - "cookie:<name>"
	// - "form:<name>"
	// Multiple sources example:
	// - "header:Authorization,cookie:myowncookie"
	TokenLookup string

	// AuthScheme to be used in the Authorization header.
	// Optional. Default value "Bearer".
	AuthScheme string

	TokenExpiry time.Duration

	RefreshExpiry time.Duration
}

func NewConfig(sk []byte, iss string, method *jwt.SigningMethodHMAC) *JWTConfig {
	return &JWTConfig{
		SigningKey:    sk,
		SigningMethod: method,
		Issuer:        iss,
		SubjectKey:    SubjectKey,
		DidKey:        DidKey,
		TokenLookup:   DefaultHeaderAuthorization,
		AuthScheme:    DefaultAuthScheme,
		TokenExpiry:   AccessExpiry,
		RefreshExpiry: RefreshExpiry,
	}
}

// CreateToken create the JWT token with all the necessary map claims
func (j *JWTConfig) CreateToken(sub atp.Aid, did string, tokenType TokenType) (string, error) {
	// Current time
	now := time.Now()

	var exp time.Duration
	switch tokenType {
	case Access:
		exp = j.TokenExpiry
	case Refresh:
		exp = j.RefreshExpiry
	default:
		return "", fmt.Errorf("invalid token type")
	}

	// Create claims with all required fields
	claims := jwt.MapClaims{
		"iat":  now.Unix(),
		"exp":  now.Add(exp).Unix(),
		"sub":  strconv.FormatUint(uint64(sub), 10),
		"did":  did,
		"iss":  j.Issuer,
		"type": tokenType,
	}

	// Create a new token with the claims
	token := jwt.NewWithClaims(j.SigningMethod, claims)

	// Sign the token with the secret key
	tokenString, err := token.SignedString(j.SigningKey)
	if err != nil {
		return "", fmt.Errorf("error signing token: %w", err)
	}

	return tokenString, nil
}

// ExtractToken get the JWT from the Authorization request header
func (j *JWTConfig) ExtractToken(r *http.Request) string {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return authHeader
	}

	authSchemeRegex := regexp.MustCompile(fmt.Sprintf(`%s\s+(.*)`, j.AuthScheme))

	match := authSchemeRegex.FindStringSubmatch(authHeader)
	if len(match) > 1 {
		return strings.TrimSpace(match[1])
	}

	return ""
}

// DecodeJWT parse the JWT and check that the token is valid
func (j *JWTConfig) DecodeJWT(tokenString string) (*jwt.Token, error) {
	// Create parser with the validator
	parser := jwt.NewParser(
		jwt.WithValidMethods([]string{j.SigningMethod.Name}),
		jwt.WithIssuedAt(),
		jwt.WithExpirationRequired(),
		jwt.WithIssuer(j.Issuer),
		jwt.WithJSONNumber(),
	)

	token, err := parser.Parse(tokenString, func(token *jwt.Token) (any, error) {
		// Return the secret key used to sign the token
		return j.SigningKey, nil
	})

	if err != nil {
		return nil, err
	}

	if !token.Valid {
		return nil, errors.New("failed to validate token")
	}

	return token, nil
}

// ValidateToken check the map claims
func ValidateToken(token *jwt.Token, tokenType TokenType) (atp.Aid, string, error) {
	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		return 0, "", fmt.Errorf("invalid token claims map")
	}

	claimsType, ok := claims["type"]
	if !ok {
		return 0, "", fmt.Errorf("missing type from claims map")
	}

	claimsTypeStr, ok := claimsType.(string)
	if !ok {
		return 0, "", fmt.Errorf("expected token type to be a string")
	}

	if TokenType(claimsTypeStr) != tokenType {
		return 0, "", fmt.Errorf("expected %s token type, got %s", tokenType, claimsType)
	}

	did, ok := claims["did"]
	if !ok {
		return 0, "", fmt.Errorf("expected user did in subject")
	}

	didStr, ok := did.(string)
	if !ok {
		return 0, "", fmt.Errorf("expected subject to be a numeric value, got %T", did)
	}

	sub, ok := claims["sub"]
	if !ok {
		return 0, "", fmt.Errorf("expected user did in subject")
	}

	// TODO: re-enable this when the data service no longer needs the JWTs (python doesn't support non-string subs)
	// jsonNum, ok := sub.(json.Number)
	// if !ok {
	// 	return 0, "", fmt.Errorf("expected subject to be a json.Number, got %T", sub)
	// }
	//
	// subInt, err := jsonNum.Int64()
	// if err != nil {
	// 	return 0, "", fmt.Errorf("failed to convert subject to integer: %w", err)
	// }
	//
	// if subInt < 0 {
	// 	return 0, "", fmt.Errorf("subject contains negative value: %d", subInt)
	// }
	//
	// maxUint := uint64(^uint(0)) // Maximum value for uint on current platform
	// if uint64(subInt) > maxUint {
	// 	return 0, "", fmt.Errorf("subject value too large for uint: %d", subInt)
	// }

	subStr, ok := sub.(string)
	if !ok {
		return 0, "", fmt.Errorf("expected subject to be a string, got %T", sub)
	}

	subInt, err := strconv.ParseUint(subStr, 10, 64)
	if err != nil {
		return 0, "", fmt.Errorf("failed to convert subject to integer: %w", err)
	}

	aid := atp.Aid(uint(subInt))

	return aid, didStr, nil
}
