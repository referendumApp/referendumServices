package auth

import "github.com/bluesky-social/indigo/models"

type TokenResponse struct {
	AccessToken  string     `json:"accessToken"`
	RefreshToken string     `json:"refreshToken"`
	TokenType    string     `json:"tokenType"`
	UserID       models.Uid `json:"userId"`
}
