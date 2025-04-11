package error

import (
	"encoding/json"
	"fmt"
	"net/http"
)

type Code string

const (
	// Authentication/Authorization errors
	ErrorCodeUnauthorized Code = "UNAUTHORIZED"
	ErrorCodeForbidden    Code = "FORBIDDEN"
	ErrorCodeInvalidToken Code = "INVALID_TOKEN"
	ErrorCodeTokenExpired Code = "TOKEN_EXPIRED"

	// Input validation errors
	ErrorCodeValidation Code = "VALIDATION_ERROR"

	// Resource errors
	ErrorCodeConflict       Code = "CONFLICT"
	ErrorCodeNotFound       Code = "NOT_FOUND"
	ErrorCodeAlreadyExists  Code = "ALREADY_EXISTS"
	ErrorCodeBadRequest     Code = "BAD_REQUEST"
	ErrorCodeUnproccessable Code = "UNPROCESSABLE"

	// Server errors
	ErrorCodeInternal           Code = "INTERNAL_ERROR"
	ErrorCodeServiceUnavailable Code = "SERVICE_UNAVAILABLE"
	ErrorDatabase               Code = "DATABASE_ERROR"
)

type FieldError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}

func (v *FieldError) Conflict() *APIError {
	return &APIError{
		Detail:     v,
		StatusCode: http.StatusConflict,
		Code:       ErrorCodeConflict,
	}
}

func (v *FieldError) Invalid() *APIError {
	return &APIError{
		Detail:     v,
		StatusCode: http.StatusUnprocessableEntity,
		Code:       ErrorCodeUnproccessable,
	}
}

func (v *FieldError) NotFound() *APIError {
	return &APIError{
		Detail:     v,
		StatusCode: http.StatusNotFound,
		Code:       ErrorCodeNotFound,
	}
}

type APIError struct {
	Detail     any               `json:"detail,omitempty"`
	Headers    map[string]string `json:"-"`
	Code       Code              `json:"code"`
	StatusCode int               `json:"-"`
}

func (e APIError) Error() string {
	if e.Detail == nil {
		return "Unexpected error occurred"
	}

	return fmt.Sprintf("Request failed: %v", e.Detail)
}

func (e APIError) WriteResponse(w http.ResponseWriter) {
	h := w.Header()
	// Set custom headers if any
	for key, value := range e.Headers {
		h.Set(key, value)
	}

	h.Set("Content-Type", "application/json")

	w.WriteHeader(e.StatusCode)

	// Write the error as JSON
	if err := json.NewEncoder(w).Encode(e); err != nil {
		http.Error(w, "Failed to encode API error to JSON", http.StatusInternalServerError)
	}
}

func BadRequest(detail string) *APIError {
	return &APIError{
		Detail:     detail,
		StatusCode: http.StatusBadRequest,
		Code:       ErrorCodeBadRequest,
	}
}

func UnproccessableEntity(detail string) *APIError {
	return &APIError{
		Detail:     detail,
		StatusCode: http.StatusUnprocessableEntity,
		Code:       ErrorCodeUnproccessable,
	}
}

func InvalidToken() *APIError {
	return &APIError{
		Detail:     "Invalid token",
		StatusCode: http.StatusBadRequest,
		Code:       ErrorCodeInvalidToken,
		Headers:    map[string]string{"WWW-Authenticate": "Bearer"},
	}
}

func ExpiredToken() *APIError {
	return &APIError{
		Detail:     "Token expired",
		StatusCode: http.StatusUnauthorized,
		Code:       ErrorCodeTokenExpired,
		Headers:    map[string]string{"WWW-Authenticate": "Bearer"},
	}
}

func Unauthorized(detail string) *APIError {
	return &APIError{
		Detail:     detail,
		StatusCode: http.StatusUnauthorized,
		Code:       ErrorCodeUnauthorized,
		Headers:    map[string]string{"WWW-Authenticate": "Bearer"},
	}
}

func NotFound(value any, resourceType string) *APIError {
	detail := fmt.Sprintf("%v %s not found", value, resourceType)
	return &APIError{
		Detail:     detail,
		StatusCode: http.StatusNotFound,
		Code:       ErrorCodeNotFound,
	}
}

func Database() *APIError {
	return &APIError{
		Detail:     "Database Query Error",
		StatusCode: http.StatusInternalServerError,
		Code:       ErrorCodeInternal,
	}
}

func InternalServer() *APIError {
	return &APIError{
		Detail:     "Internal Server Error",
		StatusCode: http.StatusInternalServerError,
		Code:       ErrorCodeInternal,
	}
}

func ServiceUnavailable() *APIError {
	return &APIError{
		Detail:     "Service Unavailable",
		StatusCode: http.StatusServiceUnavailable,
		Code:       ErrorCodeServiceUnavailable,
	}
}

func Authentication(field string, message string) *APIError {
	fieldErr := FieldError{Field: field, Message: message}

	return &APIError{
		Detail:     fieldErr,
		StatusCode: http.StatusUnauthorized,
		Code:       ErrorCodeUnauthorized,
	}
}
