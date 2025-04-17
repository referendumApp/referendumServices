package database

import (
	"context"
	"fmt"
	"log/slog"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	_ "github.com/lib/pq"

	"github.com/referendumApp/referendumServices/internal/env"
)

type DB struct {
	pool   *pgxpool.Pool
	Log    *slog.Logger
	Schema string
}

func Connect(ctx context.Context, cfg *env.Config) (*DB, error) {
	slog.Info("Setting up database connection pool")

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
		slog.Error("Failed to establish postgres connection", "conn", connStr)
		return nil, err
	}

	// Ping the database to validate the connection
	if pingErr := conn.Ping(ctx); pingErr != nil {
		slog.Error("Failed to ping database", "conn", connStr)
		return nil, pingErr
	}

	// Set connection pool settings
	poolConfig, err := pgxpool.ParseConfig(connStr)
	if err != nil {
		slog.Error("Error parsing Postgres pool config", "conn", connStr)
		return nil, err
	}

	poolConfig.MaxConns = cfg.MaxConns
	poolConfig.MinConns = cfg.MinConns
	poolConfig.MaxConnLifetime = cfg.MaxConnLife
	poolConfig.MaxConnIdleTime = cfg.MaxConnIdle

	pool, err := pgxpool.NewWithConfig(ctx, poolConfig)
	if err != nil {
		slog.Error("Error creating connection pool", "config", poolConfig)
		return nil, err
	}

	slog.Info("Successfully connected to database!")

	return &DB{pool: pool, Log: slog.Default().With("system", "db")}, nil
}

func (db *DB) WithSchema(schema string) *DB {
	return &DB{
		pool:   db.pool,
		Log:    db.Log,
		Schema: schema,
	}
}

func (db *DB) Close() {
	if db.pool != nil {
		db.pool.Close()
	}
}

func (d *DB) Ping(ctx context.Context) error {
	return d.pool.Ping(ctx)
}
