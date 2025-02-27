package database

import (
	"database/sql"
	"fmt"
	"time"

	_ "github.com/lib/pq"

	"github.com/referendumApp/referendumServices/internal/config"
)

type Database struct {
	conn *sql.DB
}

func Connect(cfg config.Config) (*Database, error) {
	// Build the connection string
	connStr := fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=disable",
		cfg.PgUser,
		cfg.PgPassword,
		cfg.PgHost,
		cfg.PgPort,
		cfg.DBName,
	)

	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, fmt.Errorf("failed to establish database connection: %v (%T)", err, err)
	}

	// Ping the database to validate the connection
	err = db.Ping()
	if err != nil {
		return nil, fmt.Errorf("failed to ping database: %v", err)
	}

	fmt.Println("Successfully connected to database!")

	// Set connection pool settings
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(time.Minute * 5)

	return &Database{
		conn: db,
	}, nil
}

func (d *Database) Close() error {
	return d.conn.Close()
}

func (d *Database) Ping() error {
	return d.conn.Ping()
}
