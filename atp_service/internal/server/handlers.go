package server

import (
	"fmt"
	"net/http"

	"github.com/referendumApp/referendumServices/internal/models"
)

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		err := fmt.Errorf("%s method not allowed", r.Method)
		http.Error(w, err.Error(), http.StatusMethodNotAllowed)
		return
	}

	if err := s.db.Ping(); err != nil {
		http.Error(w, fmt.Errorf("failed to access database: %v", err).Error(), http.StatusInternalServerError)
	}

	resp := map[string]bool{"healthy": true}
	encode(w, http.StatusOK, resp)
}

func (s *Server) handleFollow() http.Handler {
	return http.HandlerFunc(
		func(w http.ResponseWriter, r *http.Request) {
			if r.Method != http.MethodPost {
				err := fmt.Errorf("%s method not allowed", r.Method)
				http.Error(w, err.Error(), http.StatusMethodNotAllowed)
				return
			}

			req, err := decodeAndValidate[*models.FollowRequest](r)
			if err != nil {
				http.Error(w, err.Error(), http.StatusBadRequest)
				return
			}

			fmt.Println(r.Context().Value("email"))
			fmt.Println(req.UserMessage)
		},
	)
}
