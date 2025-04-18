package database

import (
	"context"
	"fmt"
	"log"
	"log/slog"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	_ "github.com/lib/pq"
	"github.com/referendumApp/referendumServices/internal/env"
)

// DB contains connection pool, logger, and schema
type DB struct {
	pool   *pgxpool.Pool
	Log    *slog.Logger
	Schema string
}

// Connect intializes a DB struct without a schema
func Connect(ctx context.Context, cfg *env.Config) (*DB, error) {
	log.Println("Setting up database connection pool")

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
		log.Printf("Failed to establish postgres connection: %s\n", connStr)
		return nil, err
	}

	// Ping the database to validate the connection
	if pingErr := conn.Ping(ctx); pingErr != nil {
		log.Printf("Failed to ping database: %s\n", connStr)
		return nil, pingErr
	}

	// Set connection pool settings
	poolConfig, err := pgxpool.ParseConfig(connStr)
	if err != nil {
		log.Printf("Error parsing Postgres pool config: %s\n", connStr)
		return nil, err
	}

	poolConfig.MaxConns = cfg.MaxConns
	poolConfig.MinConns = cfg.MinConns
	poolConfig.MaxConnLifetime = cfg.MaxConnLife
	poolConfig.MaxConnIdleTime = cfg.MaxConnIdle

	pool, err := pgxpool.NewWithConfig(ctx, poolConfig)
	if err != nil {
		log.Println("Error creating connection pool")
		return nil, err
	}

	log.Println("Successfully connected to database!")

	return &DB{pool: pool, Log: slog.Default().With("system", "db")}, nil
}

// WithSchema intializes a DB struct with a schema
func (db *DB) WithSchema(schema string) *DB {
	return &DB{
		pool:   db.pool,
		Log:    db.Log,
		Schema: schema,
	}
}

// Close shutdowns a DBs connection pool
func (db *DB) Close() {
	if db.pool != nil {
		db.pool.Close()
	}
}

// Ping checks DB connection
func (d *DB) Ping(ctx context.Context) error {
	return d.pool.Ping(ctx)
}
