// Server method for handling routers

package server

import "net/http"

func (s *Server) setupRoutes() {
	userHandler := http.NewServeMux()
	userHandler.HandleFunc("/follow", handleFollow)

	s.mux.Handle("/users/", http.StripPrefix("/users", userHandler))
}
