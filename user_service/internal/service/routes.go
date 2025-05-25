package service

import "github.com/go-chi/chi/v5"

func (s *Service) setupRoutes() {
	s.mux.Get("/health", s.handleHealth)

	s.mux.Route("/auth", func(r chi.Router) {
		r.Post("/signup", s.handleCreateUser)
		r.Post("/login", s.handleCreateSession)
		r.Post("/refresh", s.handleRefreshSession)
		r.With(s.pds.AuthorizeUser).Delete("/session", s.handleDeleteSession)
		r.With(s.pds.AuthorizeUser).Delete("/account", s.handleDeleteUser)

		r.With(s.av.AuthorizeSystemUser).Post("/system", s.handleCreateAdmin)
	})

	s.mux.Route("/user", func(r chi.Router) {
		r.Use(s.pds.AuthorizeUser)

		r.Put("/profile", s.handleUpdateUserProfile)
		r.Post("/follow", s.handleGraphFollow)

		r.Get("/profile", s.handleGetUserProfile)
		r.Get("/followers", s.handleGraphFollowers)
		r.Get("/following", s.handleGraphFollowing)
	})

	s.mux.Route("/legislator", func(r chi.Router) {
		r.Group(func(r chi.Router) {
			r.Use(s.av.AuthorizeSystemUser)
			r.Post("/", s.handleCreateLegislator)
			r.Put("/", s.handleUpdateLegislator)
			r.Delete("/", s.handleDeleteLegislator)
		})

		r.Group(func(r chi.Router) {
			// r.Use(s.pds.AuthorizeAdminOrUser)
			r.Get("/", s.handleGetLegislator)
		})
	})

	s.mux.Route("/server", func(r chi.Router) {
		r.Get("/describeServer", s.handleDescribeServer)
		// r.Get("/com.atproto.sync.subscribeRepos", s.pds.EventsHandler)
	})
}
