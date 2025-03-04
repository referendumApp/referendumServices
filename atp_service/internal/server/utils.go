package server

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/referendumApp/referendumServices/internal/domain/common"
)

// Encode and validate the response body
func encode[T any](w http.ResponseWriter, status int, v T) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("Error encoding response: %v", err)
		http.Error(w, "Failed to generate response", http.StatusInternalServerError)
	}
}

// Decode and validate the request body
func decodeAndValidate[T common.Validator](r *http.Request) (T, error) {
	var v T
	if err := json.NewDecoder(r.Body).Decode(&v); err != nil {
		return v, fmt.Errorf("invalid request body, %v", err)
	}

	if problems := v.Validate(r.Context()); len(problems) > 0 {
		return v, fmt.Errorf("invalid %T: %v", v, problems)
	}

	return v, nil
}
