package server

import (
	"context"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
)

// Server method for handling routers
func (s *Server) setupRoutes() {
	s.mux.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
		defer cancel()

		resp := map[string]bool{"healthy": false}

		err := s.db.Ping(ctx)
		if err != nil {
			encode(w, http.StatusServiceUnavailable, resp)
			return
		}

		resp["healthy"] = true
		encode(w, http.StatusOK, resp)
	})

	s.mux.Route("/xrpc", func(r chi.Router) {
		r.Route("/auth", func(r chi.Router) {
			r.Post("/signup", s.handleSignUp)
			r.Post("/login", s.handleLogin)
			r.Post("/refresh", s.handleRefresh)
		})

		r.Route("/users/bills", func(r chi.Router) {
			r.Use(s.authorizeUser)

			r.Get("/", s.handleUserFollowedBills)
			r.Post("/{billId}", s.handleBillFollow)
			r.Delete("/{billId}", s.handleBillUnfollow)
		})
	})
}
