package main

import (
	"context"
	"io"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/referendumApp/referendumServices/internal/app"
	"github.com/referendumApp/referendumServices/internal/aws"
	"github.com/referendumApp/referendumServices/internal/car"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/env-config"
	"github.com/referendumApp/referendumServices/internal/keymgr"
	"github.com/referendumApp/referendumServices/internal/pds"
	"github.com/referendumApp/referendumServices/internal/plc"
	"github.com/referendumApp/referendumServices/internal/service"
	"github.com/referendumApp/referendumServices/internal/util"
)

func run(ctx context.Context, stdout io.Writer, cfg *env.Config) error {
	// Marks the context as done when interrupt or SIGTERM signal is received
	ctx, cancel := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGINT, syscall.SIGTERM)
	defer cancel()

	logger := util.SetupLogger(ctx, stdout)

	db, err := database.Connect(ctx, cfg.DBConfig, logger)
	if err != nil {
		return err
	}
	defer db.Close()

	av := app.NewAppView(db, cfg.DBConfig.AtpDBSchema, cfg.HandleSuffix, logger)

	clients, err := aws.NewClients(ctx, cfg.Env)
	if err != nil {
		return err
	}

	pdsLogger := logger.WithGroup("pds")

	cs, err := car.NewCarStore(ctx, db, clients.S3, cfg.DBConfig.CarDBSchema, cfg.Env, cfg.CarDir, pdsLogger)
	if err != nil {
		return err
	}

	km, err := keymgr.NewKeyManager(
		ctx,
		clients.KMS,
		clients.S3,
		cfg.Env,
		cfg.KeyDir,
		cfg.RecoveryKey,
		util.RefreshExpiry,
		util.AccessExpiry-(5*time.Minute),
		pdsLogger,
	)
	if err != nil {
		return err
	}

	plc := plc.NewClient(cfg.PLCHost, km, pdsLogger)

	pds, err := pds.NewPDS(ctx, km, plc, cs, cfg.HandleSuffix, cfg.ServiceUrl, cfg.SecretKey, logger)
	if err != nil {
		return err
	}

	srv, err := service.New(ctx, av, pds, clients, logger)
	if err != nil {
		return err
	}

	return srv.Start(ctx)
}

func main() {
	ctx := context.Background()
	cfg, err := env.LoadConfig()
	if err != nil {
		log.Fatalf("Failed to load environment variables: %v", err)
	}

	if err := run(ctx, os.Stdout, cfg); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
