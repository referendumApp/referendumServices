package server

import (
	"context"
	"fmt"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"

	"github.com/referendumApp/referendumServices/internal/domain/common"
	"github.com/referendumApp/referendumServices/internal/domain/follow"
)

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	if err := s.db.Ping(); err != nil {
		http.Error(w, fmt.Errorf("failed to access database: %v", err).Error(), http.StatusInternalServerError)
	}

	resp := map[string]bool{"healthy": true}
	encode(w, http.StatusOK, resp)
}

func (s *Server) handleFollow(w http.ResponseWriter, r *http.Request) {
	req, err := decodeAndValidate[*follow.BillRequest](r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	fmt.Println(r.Context().Value("email"))
	fmt.Println(req.UserMessage)
}

func (s *Server) getBillIdAndValidate(ctx context.Context, r *http.Request) (int64, error) {
	billIdStr := chi.URLParam(r, "billId")
	billId, err := strconv.ParseInt(billIdStr, 10, 64)
	if err != nil {
		fmt.Printf("Error parsing bill ID %d: %v", billId, err)
		return 0, err
	}

	if exists, err := s.db.BillExists(ctx, billId); !exists || err != nil {
		fmt.Printf("Bill ID does not exist: %v", err)
		return 0, fmt.Errorf("bill ID %d does not exist", billId)
	}

	return billId, nil
}

func (s *Server) handleUserFollowedBills(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	userId, ok := ctx.Value("userId").(int64)
	if !ok {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	provider := &follow.UserFollowedBills{UserID: userId}
	err := s.db.PrepareAndSelect(
		ctx,
		provider,
	)
	if err != nil {
		http.Error(w, "Error getting user followed bills", http.StatusInternalServerError)
		return
	}

	encode(w, http.StatusOK, provider.Result)
}

func (s *Server) handleBillFollow(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	userId, ok := ctx.Value("userId").(int64)
	if !ok {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	billId, err := s.getBillIdAndValidate(ctx, r)
	if err != nil {
		http.Error(w, "Invalid bill ID", http.StatusBadRequest)
		return
	}

	provider := &follow.UserFollowedBills{UserID: userId, BillID: billId}

	if _, err := s.db.PrepareAndExecuteMutation(ctx, provider, common.OperationCreate); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) handleBillUnfollow(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	userId, ok := ctx.Value("userId").(int64)
	if !ok {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	billId, err := s.getBillIdAndValidate(ctx, r)
	if err != nil {
		http.Error(w, "Invalid bill ID", http.StatusBadRequest)
		return
	}

	provider := &follow.UserFollowedBills{UserID: userId, BillID: billId}

	if _, err := s.db.PrepareAndExecuteMutation(ctx, provider, common.OperationDelete); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
