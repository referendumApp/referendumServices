package service

import "github.com/go-chi/chi/v5"

func (s *Service) setupRoutes() {
	s.mux.Get("/health", s.handleHealth)

	s.mux.Route("/auth", func(r chi.Router) {
		r.Post("/signup", s.handleCreateUser)
		r.Post("/login", s.handleCreateSession)
		r.Post("/refresh", s.handleRefreshSession)

		authorize := r.With(s.pds.AuthorizeUser)
		authorize.Post("/password/reset", s.handleRefreshSession)
		authorize.Delete("/session", s.handleDeleteSession)
		authorize.Delete("/account", s.handleDeleteUser)
	})

	s.mux.Route("/users", func(r chi.Router) {
		r.Use(s.pds.AuthorizeUser)

		r.Get("/profile", s.handleGetUserProfile)
		r.Put("/profile", s.handleUserProfileUpdate)

		r.Post("/follow", s.handleGraphFollow)
		r.Get("/followers", s.handleGraphFollowers)
		r.Get("/following", s.handleGraphFollowing)
	})

	s.mux.Route("/follows", func(r chi.Router) {
		r.Use(s.pds.AuthorizeUser)

		r.Route("/public_servants", func(r chi.Router) {
			r.Post("/", s.handleGraphFollow)
			r.Delete("/{targetID}", s.handleGraphUnfollow)
		})

		r.Route("/content", func(r chi.Router) {
			r.Post("/", s.handleContentFollow)
			r.Delete("/", s.handleContentUnfollow)
		})
	})

	s.mux.Route("/votes", func(r chi.Router) {
		r.Use(s.pds.AuthorizeUser)

		r.Route("/policy_makers", func(r chi.Router) {
			r.Put("/", s.handleGraphVote)
			r.Delete("/", s.handleGraphUnvote)
		})

		r.Route("/content", func(r chi.Router) {
			r.Put("/", s.handleContentVote)
			r.Delete("/", s.handleContentUnvote)
		})
	})

	s.mux.Route("/legislators", func(r chi.Router) {
		// TODO - add system auth here
		// 		r.Use(s.pds.AuthorizeUser)

		r.Post("/", s.handleCreateLegislator)
		r.Get("/", s.handleGetLegislator)
		r.Put("/", s.handleUpdateLegislator)
		r.Delete("/", s.handleDeleteLegislator)
	})

	s.mux.Route("/server", func(r chi.Router) {
		r.Get("/describeServer", s.handleDescribeServer)
		// r.Get("/com.atproto.sync.subscribeRepos", s.pds.EventsHandler)
	})
}
