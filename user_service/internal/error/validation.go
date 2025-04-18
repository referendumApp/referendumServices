//revive:disable:exported
package error

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
)

type ValidationErrorType string

const (
	InvalidInput ValidationErrorType = "INVALID_INPUT"
	InvalidType  ValidationErrorType = "INVALID_TYPE"
	MissingField ValidationErrorType = "MISSING_FIELD"
)

type ValidationFieldError struct {
	FieldError
	Type ValidationErrorType `json:"type"`
}

func NewValidationFieldError(field string, message string, errorType ValidationErrorType) *APIError {
	detail := ValidationFieldError{
		FieldError: FieldError{
			Field:   field,
			Message: message,
		},
		Type: errorType,
	}
	return &APIError{
		Detail:     detail,
		StatusCode: http.StatusUnprocessableEntity,
		Code:       ErrorCodeValidation,
	}
}

func ValidationError(validationErrors []ValidationFieldError) *APIError {
	var detail strings.Builder
	detail.WriteString("Validation errors:")

	for i, err := range validationErrors {
		detail.WriteString(fmt.Sprintf("\n %d. Field '%s': %s (%s)",
			i+1, err.Field, err.Message, err.Type))
	}

	return &APIError{
		Detail:     detail,
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
