package util

import (
	"context"
	"encoding/json"
	"log/slog"
	"net/http"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
)

func GetAndValidatePerson(w http.ResponseWriter, ctx context.Context, log *slog.Logger) (*atp.Person, bool) {
	per, ok := ctx.Value(ContextKey).(*atp.Person)
	if !ok {
		log.Error("Invalid user in request context")
		refErr.Unauthorized("Unauthorized user").WriteResponse(w)
	}
	return per, ok
}

// Encode and validate the response body
func Encode[T any](w http.ResponseWriter, status int, log *slog.Logger, v T) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Error("Error encoding response: %v", "error", err)
		refErr.UnproccessableEntity("Unproccessable response body").WriteResponse(w)
	}
}

func DecodeAndValidate[T any](w http.ResponseWriter, r *http.Request, log *slog.Logger, v *T) error {
	if err := json.NewDecoder(r.Body).Decode(v); err != nil {
		log.Error("Failed to decode request body", "error", err)
		refErr.UnproccessableEntity("Invalid entity").WriteResponse(w)
		return err
	}

	if err := Validate.Struct(v); err != nil {
		apiErrs := HandleFieldError(err, log)
		refErr.WriteFieldErrors(w, apiErrs)
		return err
	}

	return nil
}
