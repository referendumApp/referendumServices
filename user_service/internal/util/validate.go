package util

import (
	"fmt"
	"reflect"
	"strings"
	"unicode"

	"github.com/go-playground/validator/v10"

	refErr "github.com/referendumApp/referendumServices/internal/error"
)

var Validate *validator.Validate

func init() {
	Validate = validator.New()
	Validate.RegisterTagNameFunc(func(fld reflect.StructField) string {
		jsonTag := fld.Tag.Get("json")
		parts := strings.Split(jsonTag, ",")
		if len(parts) > 0 {
			return parts[0]
		}
		return fld.Name
	})

	if err := Validate.RegisterValidation("handle", ValidateHandle); err != nil {
		panic(fmt.Sprintf("Error registering handle validator function: %v", err))
	}
	if err := Validate.RegisterValidation("username", ValidateUsername); err != nil {
		panic(fmt.Sprintf("Error registering username validator function: %v", err))
	}
	if err := Validate.RegisterValidation("did", ValidateDID); err != nil {
		panic(fmt.Sprintf("Error registering did validator function: %v", err))
	}
	if err := Validate.RegisterValidation("strongpassword", ValidateStrongPassword); err != nil {
		panic(fmt.Sprintf("Error registering strong password validator function: %v", err))
	}
}

func ValidateHandle(fl validator.FieldLevel) bool {
	handle := fl.Field().String()

	return strings.HasPrefix(handle, "at://")
}

func ValidateUsername(fl validator.FieldLevel) bool {
	if ValidateHandle(fl) {
		return true
	}

	uname := fl.Field().String()
	emailValidator := validator.New()
	err := emailValidator.Var(uname, "email")

	return err == nil
}

func ValidateDID(fl validator.FieldLevel) bool {
	did := fl.Field().String()

	return strings.HasPrefix(did, "did:plc")
}

func ValidateStrongPassword(fl validator.FieldLevel) bool {
	password := fl.Field().String()

	// Check for at least one digit
	hasDigit := false
	// Check for at least one uppercase letter
	hasUpper := false
	// Check for at least one lowercase letter
	hasLower := false

	for _, char := range password {
		if unicode.IsDigit(char) {
			hasDigit = true
		} else if unicode.IsUpper(char) {
			hasUpper = true
		} else if unicode.IsLower(char) {
			hasLower = true
		}
	}

	// Check for at least one symbol
	hasSymbol := false
	symbols := "!@#$%^&*()_+-=[]{}|;':\",./<>?"
	for _, char := range password {
		if strings.ContainsRune(symbols, char) {
			hasSymbol = true
			break
		}
	}

	return hasDigit && hasUpper && hasLower && hasSymbol
}

func HandleFieldError(e validator.FieldError) *refErr.APIError {
	var errMsg string
	var errType refErr.ValidationErrorType
	switch e.ActualTag() {
	case "required":
		errMsg = "Required field is missing"
		errType = refErr.MissingField
	case "email":
		errMsg = "Invalid email"
		errType = refErr.InvalidInput
	case "max":
		errMsg = fmt.Sprintf("Must not exceed %s characters", e.Param())
		errType = refErr.InvalidInput
	case "min":
		errMsg = fmt.Sprintf("Must be at least %s characters", e.Param())
		errType = refErr.InvalidInput
	case "strongpassword":
		errMsg = "Password must contain: \n• At least one uppercase letter (A-Z)\n• At least one digit (0-9)\n• At least one special character"
		errType = refErr.InvalidInput
	case "identifier":
		errMsg = "Invalid email or handle"
		errType = refErr.InvalidInput
	case "oneof":
		errMsg = "Invalid value found"
		errType = refErr.InvalidInput
	default:
		errMsg = "Validation failed"
		errType = refErr.InvalidInput
	}

	return refErr.NewValidationFieldError(e.Field(), errMsg, errType)
}
