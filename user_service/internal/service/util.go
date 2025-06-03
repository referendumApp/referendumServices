package service

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

var ErrUnauthorized = errors.New("unauthorized user request")
var ErrInvalidActor = errors.New("invalid actor ID")

func (s *Service) getAuthenticatedIds(ctx context.Context) (atp.Aid, string, *refErr.APIError) {
	aid, ok := ctx.Value(util.SubjectKey).(atp.Aid)
	if !ok {
		s.log.ErrorContext(ctx, ErrInvalidActor.Error(), "aid", aid)
		return 0, "", refErr.Unauthorized(ErrUnauthorized.Error())
	}
	did, ok := ctx.Value(util.DidKey).(string)
	if !ok {
		s.log.ErrorContext(ctx, "Invalid DID")
		return 0, "", refErr.Unauthorized(ErrUnauthorized.Error())
	}
	return aid, did, nil
}

func (s *Service) getAidURLParam(ctx context.Context, key string) (atp.Aid, *refErr.APIError) {
	aidStr := chi.URLParamFromCtx(ctx, key)
	aidUint, err := strconv.ParseUint(aidStr, 10, 64)
	if err != nil {
		s.log.ErrorContext(ctx, ErrInvalidActor.Error(), "aid", aidUint, "key", key)
		return 0, refErr.BadRequest(ErrInvalidActor.Error())
	}
	aid := atp.Aid(aidUint)

	return aid, nil
}

func (s *Service) handleValidationErrors(ctx context.Context, err error) *refErr.APIError {
	var valErr validator.ValidationErrors
	if errors.As(err, &valErr) {
		fieldErrs := make([]*refErr.ValidationFieldError, 0, len(valErr))
		for _, e := range valErr {
			s.log.ErrorContext(
				ctx,
				"HTTP body validation failed",
				"field",
				e.Field(),
				"validationTag",
				e.ActualTag(),
				"error",
				e.Error(),
			)
			fieldErr := refErr.HandleFieldError(e)
			fieldErrs = append(fieldErrs, fieldErr)
		}
		return refErr.ValidationAPIError(fieldErrs)
	}

	s.log.ErrorContext(ctx, "HTTP body validation failed", "err", err)
	return refErr.UnproccessableEntity("Failed to validate object: " + err.Error())
}

func (s *Service) encode(ctx context.Context, w http.ResponseWriter, status int, v any) {
	if err := util.Validate.StructCtx(ctx, v); err != nil {
		apiErr := s.handleValidationErrors(ctx, err)
		apiErr.WriteResponse(w)
		return
	}

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

	if err := util.Validate.StructCtx(ctx, v); err != nil {
		apiErr := s.handleValidationErrors(ctx, err)
		apiErr.WriteResponse(w)
		return err
	}

	return nil
}
