package server

import "github.com/go-chi/chi/v5"

// Server method for handling routers
func (s *Server) setupRoutes() {
	s.mux.Get("/health", s.handleHealth)

	s.mux.Route("/xrpc", func(r chi.Router) {
		r.Route("/auth", func(r chi.Router) {
			r.Post("/signup", s.handleCreateAccount)
			r.Post("/login", s.handleCreateSession)
			r.Post("/refresh", s.handleRefreshSession)
		})

		r.Route("/user", func(r chi.Router) {
			r.Use(s.pds.AuthorizeUser)

			r.Delete("/", s.handleUserDelete)
			r.Put("/profile", s.handleProfileUpdate)
			r.Post("/follow", s.handleGraphFollow)

			r.Get("/profile", s.handleGetProfile)
			r.Get("/followers", s.handleGraphFollowers)
			r.Get("/following", s.handleGraphFollowing)
		})

		r.Get("/com.atproto.server.describeServer", s.handleDescribeServer)
		r.Get("/com.atproto.sync.subscribeRepos", s.pds.EventsHandler)
	})
}
