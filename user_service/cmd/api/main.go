package main

import (
	"context"
	"crypto/rand"
	"io"
	"log"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/whyrusleeping/go-did"

	"github.com/referendumApp/referendumServices/internal/car"
	"github.com/referendumApp/referendumServices/internal/config"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/plc"
	"github.com/referendumApp/referendumServices/internal/server"
)

func run(ctx context.Context, stderr io.Writer) error {
	// Marks the context as done when interrupt or SIGTERM signal is received
	ctx, cancel := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGINT, syscall.SIGTERM)
	defer cancel()

	envlog := slog.Default().With("system", "environment")
	dblog := slog.Default().With("system", "database")
	pdslog := slog.Default().With("system", "pds")

	cfg := config.LoadConfigFromEnv(envlog)

	db, err := database.Connect(ctx, cfg, dblog)
	if err != nil {
		return err
	}

	pdslog.Info("Generating private key")
	servkey, err := did.GeneratePrivKey(rand.Reader, did.KeyTypeSecp256k1)
	if err != nil {
		pdslog.Error("Failed to generate private key")
		return err
	}
	pdslog.Info("Successfully generated private key!")

	car, err := car.Initialize(cfg, pdslog)
	if err != nil {
		db.Close()
		return err
	}

	plc := plc.Server{Host: cfg.PLCHost, C: &http.Client{}}

	srv, err := server.New(pdslog, db, servkey, cfg, car, plc)
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
	if err := run(ctx, os.Stderr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
