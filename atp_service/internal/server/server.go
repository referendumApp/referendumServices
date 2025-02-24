package server

import (
	"context"
	"fmt"
  "io"
	"net/http"
  "sync"
	"time"
)

type Server struct {
	mux *http.ServeMux
  secretKey []byte
}

func NewServer(getenv func(string) string) http.Handler {
  srv := &Server{
    mux: http.NewServeMux(),
    secretKey: []byte(getenv("SECRET_KEY")),
  }

	srv.setupRoutes()
  handler := srv.authorizeUser()
  return handler
}

func StartServer(ctx context.Context, handler http.Handler, stderr io.Writer) {
	port := ":8080"

	httpServer := &http.Server{
		Addr:         port,
		Handler:      handler,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  15 * time.Second,
	}

	go func() {
		fmt.Printf("Server starting on port %s\n", port)
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Fprintf(stderr, "Error listening and serving: %s", err)
		}
	}()

  var wg sync.WaitGroup
  wg.Add(1)
  go func() {
    defer wg.Done()
    <-ctx.Done()

    shutdownCtx := context.Background()
    shutdownCtx, cancel := context.WithTimeout(shutdownCtx, 5 * time.Second)
    defer cancel()
    if err := httpServer.Shutdown(shutdownCtx); err != nil {
      fmt.Fprintf(stderr, "Error shutting down http server: %s", err)
    }
  }()
  wg.Wait()

	fmt.Println("Server stopped")
}
