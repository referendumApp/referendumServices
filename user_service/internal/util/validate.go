package util

import (
	"fmt"
	"reflect"
	"regexp"
	"strings"
	"unicode"

	"github.com/go-playground/validator/v10"
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
