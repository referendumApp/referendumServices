//revive:disable:exported
package error

import (
	"encoding/json"
	"net/http"
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
	// detail := ValidationFieldError{
	// 	FieldError: FieldError{
	// 		Field:   field,
	// 		Message: message,
	// 	},
	// 	Type:     errorType,
	// 	Criteria: criteria,
	// }
	// return &APIError{
	// 	Detail:     detail,
	// 	StatusCode: http.StatusUnprocessableEntity,
	// 	Code:       ErrorCodeValidation,
	// }
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
