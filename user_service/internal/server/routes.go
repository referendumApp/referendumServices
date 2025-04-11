package server

import "github.com/go-chi/chi/v5"

// Server method for handling routers
func (s *Server) setupRoutes() {
	s.mux.Get("/health", s.pds.HandleHealth)

	s.mux.Route("/xrpc", func(r chi.Router) {
		r.Route("/auth", func(r chi.Router) {
			r.Post("/signup", s.pds.HandleSignUp)
			r.Post("/login", s.handleLogin)
			r.Post("/refresh", s.handleRefresh)
		})

		r.Route("/user", func(r chi.Router) {
			r.Use(s.authorizeUser)

			r.Delete("/", s.pds.HandleUserDelete)
			r.Put("/profile", s.pds.HandleProfileUpdate)
			r.Post("/follow", s.pds.HandleGraphFollow)

			r.Get("/profile", s.av.HandleGetProfile)
			r.Get("/followers", s.av.HandleGraphFollowers)
			r.Get("/following", s.av.HandleGraphFollowing)
		})

		r.Get("/com.atproto.server.describeServer", s.pds.HandleAtprotoDescribeServer)
		r.Get("/com.atproto.sync.subscribeRepos", s.pds.EventsHandler)
	})
}
