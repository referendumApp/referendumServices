package main

import (
	"context"
	"io"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/env-config"
	"github.com/referendumApp/referendumServices/internal/server"
	"github.com/referendumApp/referendumServices/internal/util"
)

func run(ctx context.Context, stdout io.Writer) error {
	// Marks the context as done when interrupt or SIGTERM signal is received
	ctx, cancel := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGINT, syscall.SIGTERM)
	defer cancel()

	cfg := env.LoadConfigFromEnv()

	logger := util.SetupLogger(ctx, stdout)

	db, err := database.Connect(ctx, cfg, logger)
	if err != nil {
		return err
	}

	srv, err := server.New(ctx, cfg, db, logger)
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
	if err := run(ctx, os.Stdout); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
