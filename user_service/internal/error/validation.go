//revive:disable:exported
package error

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/go-playground/validator/v10"
)

type ValidationErrorType string

const (
	InvalidInput ValidationErrorType = "INVALID_INPUT"
	InvalidType  ValidationErrorType = "INVALID_TYPE"
	MissingField ValidationErrorType = "MISSING_FIELD"
)

type ValidationFieldError struct {
	FieldError
	Type     ValidationErrorType `json:"type"`
	Criteria []string            `json:"criteria"`
}

func NewValidationFieldError(
	field string,
	message string,
	errorType ValidationErrorType,
	criteria ...string,
) *ValidationFieldError {
	if criteria == nil {
		criteria = []string{}
	}
	return &ValidationFieldError{
		FieldError: FieldError{
			Field:   field,
			Message: message,
		},
		Type:     errorType,
		Criteria: criteria,
	}
}

func ValidationAPIError(validationErrors []*ValidationFieldError) *APIError {
	return &APIError{
		Detail:     validationErrors,
		StatusCode: http.StatusUnprocessableEntity,
		Code:       ErrorCodeValidation,
	}
}

func WriteFieldErrors(w http.ResponseWriter, fieldErrs []*APIError) {
	h := w.Header()

	h.Set("Content-Type", "application/json")

	w.WriteHeader(http.StatusUnprocessableEntity)

	// Write the error as JSON
	if err := json.NewEncoder(w).Encode(fieldErrs); err != nil {
		http.Error(w, "Failed to encode API error to JSON", http.StatusInternalServerError)
	}
}

// HandleFieldError initializes 'ValidationFieldError' struct with the msg and type based on the validation error
func HandleFieldError(e validator.FieldError) *ValidationFieldError {
	var errMsg string
	var errType ValidationErrorType
	var criteria []string
	switch e.ActualTag() {
	case "required":
		errMsg = e.StructField() + " is required"
		errType = MissingField
	case "name":
		errMsg = "Invalid name format"
		errType = InvalidInput
		criteria = []string{"No special characters allowed", "No numbers allowed", "Check for consecutive spaces"}
	case "handle":
		errMsg = "Invalid handle format"
		errType = InvalidInput
	case "email":
		errMsg = "Invalid email format"
		errType = InvalidInput
	case "max":
		errMsg = fmt.Sprintf("%s must not exceed %s characters", e.StructField(), e.Param())
		errType = InvalidInput
	case "min":
		errMsg = fmt.Sprintf("%s must be at least %s characters", e.StructField(), e.Param())
		errType = InvalidInput
	case "strongpassword":
		errMsg = "Password must contain:"
		errType = InvalidInput
		criteria = []string{
			"At least one uppercase letter (A-Z)",
			"At least one digit (0-9)",
			"At least one special character",
		}
	case "username":
		errMsg = "Invalid email or handle"
		errType = InvalidInput
	case "oneof":
		errMsg = "Invalid value found"
		errType = InvalidInput
	default:
		errMsg = "Validation failed"
		errType = InvalidInput
	}

	return NewValidationFieldError(e.Field(), errMsg, errType, criteria...)
}
