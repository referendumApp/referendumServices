package auth

import (
	"context"
	"net/mail"

	refErr "github.com/referendumApp/referendumServices/internal/error"
)

const (
	GRANTTYPE = "grantType"
	EMAIL     = "email"
	NAME      = "name"
	HANDLE    = "handle"
	PASSWORD  = "password"
)

type SignUpRequest struct {
	RecoveryKey *string `json:"recoveryKey"`
	Email       string  `json:"email"`
	Name        string  `json:"name"`
	Handle      string  `json:"handle"`
	Password    string  `json:"password"`
}

func (s *SignUpRequest) Validate(ctx context.Context) *refErr.APIError {
	if s.Email == "" {
		fieldErr := refErr.NewValidationFieldError(EMAIL, "Required field is missing", refErr.MissingField)
		return fieldErr.Raise()
	}

	if _, err := mail.ParseAddress(s.Email); err != nil {
		fieldErr := refErr.NewValidationFieldError(EMAIL, err.Error(), refErr.InvalidInput)
		return fieldErr.Raise()
	}

	if len(s.Email) > 100 {
		fieldErr := refErr.NewValidationFieldError(EMAIL, "Email must not exceed 100 characters", refErr.InvalidInput)
		return fieldErr.Raise()
	}

	if s.Name == "" {
		fieldErr := refErr.NewValidationFieldError(NAME, "Required field is missing", refErr.MissingField)
		return fieldErr.Raise()
	}

	if len(s.Name) > 100 {
		fieldErr := refErr.NewValidationFieldError(NAME, "Name must not exceed 100 characters", refErr.InvalidInput)
		return fieldErr.Raise()
	}

	if s.Handle == "" {
		fieldErr := refErr.NewValidationFieldError(HANDLE, "Required field is missing", refErr.MissingField)
		return fieldErr.Raise()
	}

	if len(s.Handle) > 100 {
		fieldErr := refErr.NewValidationFieldError(HANDLE, "Name must not exceed 100 characters", refErr.InvalidInput)
		return fieldErr.Raise()
	}

	if len(s.Password) < 8 {
		fieldErr := refErr.NewValidationFieldError(PASSWORD, "Password must be at least 8 characters", refErr.InvalidInput)
		return fieldErr.Raise()
	}

	if len(s.Password) > 100 {
		fieldErr := refErr.NewValidationFieldError(PASSWORD, "Password must not exceed 100 characters", refErr.InvalidInput)
		return fieldErr.Raise()
	}

	return nil
}

type LoginRequest struct {
	GrantType string
	Email     string
	Password  string
}

func (l *LoginRequest) Validate(ctx context.Context) *refErr.APIError {
	if l.GrantType != "password" {
		return refErr.BadRequest("Invalid grant type")
	}

	// Validate required fields
	if l.Email == "" || l.Password == "" {
		return refErr.Authentication(EMAIL, "Email or password not found")
	}

	if _, err := mail.ParseAddress(l.Email); err != nil {
		fieldErr := refErr.NewValidationFieldError(EMAIL, err.Error(), refErr.InvalidInput)
		return fieldErr.Raise()
	}

	return nil
}

type RefreshRequest struct {
	RefreshToken string `json:"refreshToken"`
}

func (r *RefreshRequest) Validate(ctx context.Context) *refErr.APIError {
	if r.RefreshToken == "" {
		fieldErr := refErr.NewValidationFieldError("refreshToken", "Required field is missing", refErr.MissingField)
		return fieldErr.Raise()
	}

	return nil
}
