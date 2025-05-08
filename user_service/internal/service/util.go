package service

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"

	"github.com/go-playground/validator/v10"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

var ErrUnauthorized = errors.New("unauthorized user request")

func (s *Service) getAndValidatePerson(ctx context.Context) (atp.Uid, string, *refErr.APIError) {
	uid, ok := ctx.Value(util.SubjectKey).(atp.Uid)
	if !ok {
		s.log.ErrorContext(ctx, "Invalid user ID", "uid", uid)
		return 0, "", refErr.Unauthorized(ErrUnauthorized.Error())
	}
	did, ok := ctx.Value(util.DidKey).(string)
	if !ok {
		s.log.ErrorContext(ctx, "Invalid DID")
		return 0, "", refErr.Unauthorized(ErrUnauthorized.Error())
	}
	return uid, did, nil
}

func (s *Service) handleValidationErrors(ctx context.Context, err error) *refErr.APIError {
	var valErr validator.ValidationErrors
	if errors.As(err, &valErr) {
		fieldErrs := make([]*refErr.ValidationFieldError, 0, len(valErr))
		for _, e := range valErr {
			s.log.ErrorContext(
				ctx,
				"Request validation failed",
				"field",
				e.Field(),
				"valdationTag",
				e.ActualTag(),
				"error",
				e.Error(),
			)
			fieldErr := refErr.HandleFieldError(e)
			fieldErrs = append(fieldErrs, fieldErr)
		}
		return refErr.ValidationAPIError(fieldErrs)
	}
	return nil
}

func (s *Service) encode(ctx context.Context, w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		s.log.ErrorContext(ctx, "Error encoding response: %v", "error", err)
		refErr.UnproccessableEntity("Unproccessable response body").WriteResponse(w)
		return
	}
}

func (s *Service) decodeAndValidate(ctx context.Context, w http.ResponseWriter, body io.ReadCloser, v any) error {
	if err := json.NewDecoder(body).Decode(v); err != nil {
		s.log.ErrorContext(ctx, "Failed to decode request body", "error", err)
		refErr.UnproccessableEntity("Invalid entity").WriteResponse(w)
		return err
	}

	if err := util.Validate.Struct(v); err != nil {
		apiErr := s.handleValidationErrors(ctx, err)
		apiErr.WriteResponse(w)
		return err
	}

	return nil
}
