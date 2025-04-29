package server

import (
	"bufio"
	"fmt"
	"net"
	"net/http"
	"time"
)

// CustomResponseWriter wrapper around 'http.ResponseWriter' to track the status code of the request
type CustomResponseWriter struct {
	http.ResponseWriter
	StatusCode int
}

// WriteHeader wrapper around 'WriteHeader' method to write the status code
func (rw *CustomResponseWriter) WriteHeader(code int) {
	rw.StatusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Hijack required for websockets
func (rw *CustomResponseWriter) Hijack() (net.Conn, *bufio.ReadWriter, error) {
	if hijacker, ok := rw.ResponseWriter.(http.Hijacker); ok {
		return hijacker.Hijack()
	}
	return nil, nil, fmt.Errorf("underlying ResponseWriter does not implement http.Hijacker")
}

func getOrCreateCustomWriter(w http.ResponseWriter) *CustomResponseWriter {
	if customWriter, ok := w.(*CustomResponseWriter); ok {
		return customWriter
	}
	return &CustomResponseWriter{
		ResponseWriter: w,
		StatusCode:     http.StatusOK,
	}
}

func (s *Server) logRequest(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		startTime := time.Now()

		// Wrap the ResponseWriter so we can include the status code in our logs
		rw := getOrCreateCustomWriter(w)

		// Log request details
		s.log.InfoContext(
			r.Context(),
			"Request started",
			"method",
			r.Method,
			"path",
			r.URL.Path,
			"address",
			r.RemoteAddr,
		)

		// Call the next handler
		next.ServeHTTP(rw, r)

		// Log completion time
		duration := fmt.Sprintf("%d ms", time.Since(startTime).Milliseconds())
		s.log.InfoContext(
			r.Context(),
			"Request completed",
			"method",
			r.Method,
			"path",
			r.URL.Path,
			"status",
			rw.StatusCode,
			"duration",
			duration,
		)
	})
}
