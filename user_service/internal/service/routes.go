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
	})

	s.mux.Route("/user", func(r chi.Router) {
		r.Use(s.pds.AuthorizeUser)

		r.Put("/profile", s.handleUserProfileUpdate)
		r.Post("/follow", s.handleGraphFollow)

		r.Get("/profile", s.handleGetUserProfile)
		r.Get("/followers", s.handleGraphFollowers)
		r.Get("/following", s.handleGraphFollowing)
	})

	s.mux.Route("/legislator", func(r chi.Router) {
		// TODO - add system auth here
		// 		r.Use(s.pds.AuthorizeUser)

		r.Post("/", s.handleCreateLegislator)
		r.Get("/", s.handleGetLegislator)
		// 		r.Put("/", s.handleLegislatorUpdate)
		// 		r.Delete("/", s.handleDeleteLegislator)
	})

	s.mux.Route("/server", func(r chi.Router) {
		r.Get("/describeServer", s.handleDescribeServer)
		// r.Get("/com.atproto.sync.subscribeRepos", s.pds.EventsHandler)
	})
}
