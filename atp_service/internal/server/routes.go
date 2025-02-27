package server

// Server method for handling routers
func (s *Server) setupRoutes() {
	s.mux.HandleFunc("/health", s.handleHealth)

	s.mux.Handle("/users/follow", s.authorizeUser(s.handleFollow()))
}
