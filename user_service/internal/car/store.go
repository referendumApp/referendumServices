package car

import (
	"fmt"
	"log/slog"
	"os"

	"github.com/bluesky-social/indigo/carstore"
	"github.com/bluesky-social/indigo/util/cliutil"

	"github.com/referendumApp/referendumServices/internal/config"
)

func Initialize(cfg config.Config, log *slog.Logger) (carstore.CarStore, error) {
	log.Info("Setting up CAR store")

	connStr := fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=disable",
		cfg.PgUser,
		cfg.PgPassword,
		cfg.PgHost,
		cfg.PgPort,
		cfg.CarDBName,
	)

	if err := os.MkdirAll(cfg.CarDir, os.ModePerm); err != nil {
		log.Error("Error creating CAR store directory", "dir", cfg.CarDir)
		return nil, err
	}

	csdb, err := cliutil.SetupDatabase(connStr, cfg.CarMaxConns)
	if err != nil {
		log.Error("Error setting up CAR database", "conn", connStr)
		return nil, err
	}

	log.Info("Successfully setup CAR store!")

	return carstore.NewCarStore(csdb, []string{cfg.CarDir})
}
