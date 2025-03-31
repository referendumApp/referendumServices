package error

import (
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

func (v *ValidationFieldError) Raise() *APIError {
	return &APIError{
		Detail:     v,
		StatusCode: http.StatusUnprocessableEntity,
		Code:       ErrorCodeValidation,
	}
}

func NewValidationFieldError(field, message string, errorType ValidationErrorType) ValidationFieldError {
	return ValidationFieldError{
		FieldError: FieldError{
			Field:   field,
			Message: message,
		},
		Type: errorType,
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
