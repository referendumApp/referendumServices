package server

import (
	"context"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"

	"github.com/referendumApp/referendumServices/internal/domain/follow"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	repo "github.com/referendumApp/referendumServices/internal/repository"
)

func (s *Server) getBillIdAndValidate(ctx context.Context, w http.ResponseWriter, r *http.Request) (int64, error) {
	billIdStr := chi.URLParam(r, "billId")
	billId, err := strconv.ParseInt(billIdStr, 10, 64)
	if err != nil {
		s.log.Error("Error parsing bill ID", "error", err, "id", billId)
		refErr.UnproccessableEntity("Invalid bill ID").WriteResponse(w)
		return 0, err
	}

	if exists, err := s.db.BillExists(ctx, billId); !exists || err != nil {
		s.log.Error("Bill ID does not exist", "error", err)
		refErr.NotFound(billId, "bill ID").WriteResponse(w)
		return 0, err
	}

	return billId, nil
}

func (s *Server) handleUserFollowedBills(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	user, ok := s.getAndValidateUser(w, ctx)
	if !ok {
		return
	}

	bills, err := s.db.GetUserFollowedBills(ctx, user.ID)
	if err != nil {
		s.log.Error("Error getting user followed bills", "error", err)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	encode(w, http.StatusOK, bills)
}

func (s *Server) handleBillFollow(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	user, ok := s.getAndValidateUser(w, ctx)
	if !ok {
		return
	}

	billId, err := s.getBillIdAndValidate(ctx, w, r)
	if err != nil {
		return
	}

	provider := &follow.UserFollowedBills{UserID: user.ID, BillID: billId}

	if err := s.db.Create(ctx, provider); err != nil {
		s.log.Error("Failed to follow bill", "error", err, "id", billId)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) handleBillUnfollow(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	user, ok := s.getAndValidateUser(w, ctx)
	if !ok {
		return
	}

	billId, err := s.getBillIdAndValidate(ctx, w, r)
	if err != nil {
		return
	}

	// provider := &follow.UserFollowedBills{UserID: user.ID, BillID: billId}
	filters := []repo.Filter{{Column: "user_id", Op: repo.Eq, Value: user.ID}, {Column: "bill_id", Op: repo.Eq, Value: billId}}

	if err := s.db.Delete(ctx, follow.UserFollowedBills{}, filters...); err != nil {
		s.log.Error("Failed to unfollow bill", "error", err, "id", billId)
		refErr.InternalServer().WriteResponse(w)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
