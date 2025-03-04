package server

import "github.com/go-chi/chi/v5"

// Server method for handling routers
func (s *Server) setupRoutes() {
	s.mux.Get("/health", s.handleHealth)

	s.mux.Route("/users", func(r chi.Router) {
		r.Use(s.authorizeUser)

		r.Route("/bills", func(r chi.Router) {
			r.Get("/", s.handleUserFollowedBills)
			r.Post("/{billId}", s.handleBillFollow)
			r.Delete("/{billId}", s.handleBillUnfollow)
		})

		r.Post("/follow", s.handleFollow)
	})
}
