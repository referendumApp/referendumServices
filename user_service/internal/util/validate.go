package util

import (
	"fmt"
	"reflect"
	"regexp"
	"strings"
	"unicode"

	"github.com/go-playground/validator/v10"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

// Validate new instance of a go-playground validator
var Validate *validator.Validate

var (
	nameRegex   = regexp.MustCompile(`^[a-zA-Z]+([ ]?[a-zA-Z]+)*$`)
	handleRegex = regexp.MustCompile(`^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]([a-z0-9-]{0,61}[a-z0-9])?$`)
	didRegex    = regexp.MustCompile(`^did:[a-z]+:(?:[a-zA-Z0-9._:%-]*(?:%[0-9A-Fa-f]{2})?[a-zA-Z0-9._-]*)$`)
)

const specialCharacters = `!@#$%^&*()_-+=[]{};:'"\|,.<>?/~`

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

	if err := Validate.RegisterValidation("name", ValidateName); err != nil {
		panic(fmt.Sprintf("Error registering handle validator function: %v", err))
	}
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

// ValidateName checks that the name is formatted correctly
func ValidateName(fl validator.FieldLevel) bool {
	name := fl.Field().String()

	return nameRegex.MatchString(name)
}

// ValidateHandle checks that the handle is formatted correctly
func ValidateHandle(fl validator.FieldLevel) bool {
	handle := fl.Field().String()

	return handleRegex.MatchString(handle)
}

// ValidateUsername applies validation based on either the handle or email
func ValidateUsername(fl validator.FieldLevel) bool {
	if ValidateHandle(fl) {
		return true
	}

	uname := fl.Field().String()
	emailValidator := validator.New()
	err := emailValidator.Var(uname, "email")

	return err == nil
}

// ValidateDID checks for the appropriate format
func ValidateDID(fl validator.FieldLevel) bool {
	did := fl.Field().String()

	return didRegex.MatchString(did)
}

// ValidateStrongPassword checks for the password requirements
func ValidateStrongPassword(fl validator.FieldLevel) bool {
	password := fl.Field().String()

	// Check for at least one digit
	var hasDigit bool
	// Check for at least one uppercase letter
	var hasUpper bool
	// Check for at least one lowercase letter
	var hasLower bool

	for _, char := range password {
		switch {
		case unicode.IsDigit(char):
			hasDigit = true
		case unicode.IsUpper(char):
			hasUpper = true
		case unicode.IsLower(char):
			hasLower = true
		}
	}

	// Check for at least one symbol
	var hasSymbol bool
	if strings.ContainsAny(password, specialCharacters) {
		hasSymbol = true
	}

	return hasDigit && hasUpper && hasLower && hasSymbol
}

// HandleFieldError initializes 'APIError' struct with the msg and type based on the validation error
func HandleFieldError(e validator.FieldError) *refErr.APIError {
	var errMsg string
	var errType refErr.ValidationErrorType
	var criteria []string
	switch e.ActualTag() {
	case "required":
		errMsg = e.StructField() + " is required"
		errType = refErr.MissingField
	case "name":
		errMsg = "Invalid name format"
		errType = refErr.InvalidInput
		criteria = []string{"No special characters allowed", "No numbers allowed", "Check for consecutive spaces"}
	case "handle":
		errMsg = "Invalid handle format"
		errType = refErr.InvalidInput
	case "email":
		errMsg = "Invalid email format"
		errType = refErr.InvalidInput
	case "max":
		errMsg = fmt.Sprintf("%s must not exceed %s characters", e.StructField(), e.Param())
		errType = refErr.InvalidInput
	case "min":
		errMsg = fmt.Sprintf("%s must be at least %s characters", e.StructField(), e.Param())
		errType = refErr.InvalidInput
	case "strongpassword":
		errMsg = "Password must contain:"
		errType = refErr.InvalidInput
		criteria = []string{
			"At least one uppercase letter (A-Z)",
			"At least one digit (0-9)",
			"At least one special character",
		}
	case "username":
		errMsg = "Invalid email or handle"
		errType = refErr.InvalidInput
	case "oneof":
		errMsg = "Invalid value found"
		errType = refErr.InvalidInput
	default:
		errMsg = "Validation failed"
		errType = refErr.InvalidInput
	}

	return refErr.NewValidationFieldError(e.Field(), errMsg, errType, criteria...)
}
