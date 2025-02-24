package server

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/referendumApp/referendumServices/internal/models"
)

func encode[T any](w http.ResponseWriter, status int, v T) error {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		return fmt.Errorf("error encoding response, %v", err)
	}

	return nil
}

func decodeAndValidate[T models.Validator](r *http.Request) (T, error) {
	var v T
	if err := json.NewDecoder(r.Body).Decode(&v); err != nil {
		return v, fmt.Errorf("invalid request body, %v", err)
	}

	if problems := v.Validate(r.Context()); len(problems) > 0 {
		return v, fmt.Errorf("invalid %T: %v", v, problems)
	}

	return v, nil
}
