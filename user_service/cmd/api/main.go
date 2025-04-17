package main

import (
	"context"
	"crypto/rand"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/whyrusleeping/go-did"

	"github.com/referendumApp/referendumServices/internal/car"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/env"
	"github.com/referendumApp/referendumServices/internal/plc"
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

	slog.Info("Generating private key")
	servkey, err := did.GeneratePrivKey(rand.Reader, did.KeyTypeSecp256k1)
	if err != nil {
		slog.Error("Failed to generate private key")
		return err
	}
	slog.Info("Successfully generated private key!")

	car, err := car.NewCarStore(ctx, cfg, db)
	if err != nil {
		db.Close()
		return err
	}

	plc := plc.Server{Host: cfg.PLCHost, C: &http.Client{}}

	srv, err := server.New(db, servkey, cfg, car, plc)
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
		slog.Error("Failed to start server", "error", err)
		os.Exit(1)
	}
}
