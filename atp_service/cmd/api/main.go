package main

import (
	"context"
	"io"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/referendumApp/referendumServices/internal/service"
)

func run(ctx context.Context, stderr io.Writer) error {
	// Marks the context as done when interrupt or SIGTERM signal is received
	ctx, cancel := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGINT, syscall.SIGTERM)
	defer cancel()

	serv, err := service.New(ctx, stderr)

	if err != nil {
		return err
	}

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := serv.Shutdown(shutdownCtx); err != nil {
		return err
	}

	return nil
}

func main() {
	ctx := context.Background()
	if err := run(ctx, os.Stderr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
