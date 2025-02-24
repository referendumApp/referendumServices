package server

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"regexp"
	"strings"

	"github.com/golang-jwt/jwt/v5"
)

type EmailKey string

const ConfigEmailKey EmailKey = "email"

var bearerRegex = regexp.MustCompile(`Bearer\s+(.*)`)

func extractToken(r *http.Request) string {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return authHeader
	}

	match := bearerRegex.FindStringSubmatch(authHeader)
	if len(match) > 1 {
		return strings.TrimSpace(match[1])
	}

	return ""
}

func decodeJWT(tokenString string, secretKey []byte) (jwt.MapClaims, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		// Validate the algorithm is what we expect
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, errors.New("unexpected signing method")
		}

		// Return the secret key used to sign the token
		return secretKey, nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		return claims, nil
	}

	return nil, errors.New("failed to validate token")
}

func (s *Server) authorizeUser() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		accessToken := extractToken(r)
		if accessToken == "" {
			http.Error(w, "Token not found", http.StatusUnauthorized)
			return
		}

		claims, err := decodeJWT(accessToken, s.secretKey)
		if err != nil {
			http.Error(w, fmt.Errorf("invalid access token: %s", err).Error(), http.StatusUnauthorized)
			return
		}

		if tokenType, ok := claims["type"].(string); !ok || tokenType != "access" {
			http.Error(w, "Invalid token type for access token", http.StatusUnauthorized)
			return
		}

		email, ok := claims["sub"].(string)
		if !ok {
			http.Error(w, "Missing email in access token", http.StatusUnauthorized)
			return
		}
		ctx := context.WithValue(r.Context(), ConfigEmailKey, email)
		r = r.WithContext(ctx)

		s.mux.ServeHTTP(w, r)
	})
}
