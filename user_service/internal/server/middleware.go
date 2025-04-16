package server

import (
	"bufio"
	"fmt"
	"net"
	"net/http"
	"time"
)

type CustomResponseWriter struct {
	http.ResponseWriter
	StatusCode int
}

func (rw *CustomResponseWriter) WriteHeader(code int) {
	rw.StatusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

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
			"urlPath",
			r.URL.Path,
			"address",
			r.RemoteAddr,
		)

		// Call the next handler
		next.ServeHTTP(rw, r)

		// Log completion time
		duration := time.Since(startTime)
		s.log.InfoContext(
			r.Context(),
			"Request completed",
			"method",
			r.Method,
			"urlPath",
			r.URL.Path,
			"status",
			rw.StatusCode,
			"duration",
			duration,
		)
	})
}
