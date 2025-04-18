package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/env-config"
	"github.com/referendumApp/referendumServices/internal/server"
)

func run(ctx context.Context) error {
	// Marks the context as done when interrupt or SIGTERM signal is received
	ctx, cancel := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGINT, syscall.SIGTERM)
	defer cancel()

	cfg := env.LoadConfigFromEnv()

	db, err := database.Connect(ctx, cfg)
	if err != nil {
		return err
	}

	srv, err := server.New(ctx, cfg, db)
	if err != nil {
		return err
	}

	if err := srv.Start(ctx); err != nil {
		return err
	}

	return nil
}

func main() {
	ctx := context.Background()
	if err := run(ctx); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
