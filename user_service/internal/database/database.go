package database

import (
	"context"
	"fmt"
	"log/slog"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	_ "github.com/lib/pq"

	"github.com/referendumApp/referendumServices/internal/config"
)

type Database struct {
	pool   *pgxpool.Pool
	log    *slog.Logger
	schema string
}

func Connect(ctx context.Context, cfg config.Config, log *slog.Logger) (*Database, error) {
	log.Info("Setting up database connection pool")

	// Build the connection string
	connStr := fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=disable",
		cfg.PgUser,
		cfg.PgPassword,
		cfg.PgHost,
		cfg.PgPort,
		cfg.DBName,
	)

	conn, err := pgx.Connect(ctx, connStr)
	if err != nil {
		log.Error("Failed to establish postgres connection", "conn", connStr)
		return nil, err
	}

	// Ping the database to validate the connection
	if pingErr := conn.Ping(ctx); pingErr != nil {
		log.Error("Failed to ping database", "conn", connStr)
		return nil, pingErr
	}

	// Set connection pool settings
	poolConfig, err := pgxpool.ParseConfig(connStr)
	if err != nil {
		log.Error("Error parsing Postgres pool config", "conn", connStr)
		return nil, err
	}

	poolConfig.MaxConns = cfg.MaxConns
	poolConfig.MinConns = cfg.MinConns
	poolConfig.MaxConnLifetime = cfg.MaxConnLife
	poolConfig.MaxConnIdleTime = cfg.MaxConnIdle

	pool, err := pgxpool.NewWithConfig(ctx, poolConfig)
	if err != nil {
		log.Error("Error creating connection pool", "config", poolConfig)
		return nil, err
	}

	log.Info("Successfully connected to database!")

	return &Database{pool: pool, log: log, schema: "atproto"}, nil
}

func (db *Database) Close() {
	if db.pool != nil {
		db.pool.Close()
	}
}

func (d *Database) Ping(ctx context.Context) error {
	return d.pool.Ping(ctx)
}
