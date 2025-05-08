package testutil

import (
	"bytes"
	"context"
	"database/sql"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/ory/dockertest/v3"
	"github.com/ory/dockertest/v3/docker"
	"github.com/referendumApp/referendumServices/internal/env-config"
)

var (
	dbOnce       sync.Once
	postgresDB   *sql.DB
	pgContainer  *dockertest.Resource
	postgresPort string
)

// PostgresContainer holds information about the postgres container
type PostgresContainer struct {
	DB          *sql.DB
	Port        string
	DBSchema    string
	pgContainer *dockertest.Resource
}

// SetupPostgres creates a postgres container and runs migrations
func (d *Docker) SetupPostgres(ctx context.Context, cfg *env.DBConfig) (*PostgresContainer, error) {
	var (
		migrationContainer *dockertest.Resource
		dbErr              error
		code               int
	)

	dbOnce.Do(func() {
		pgContainer, dbErr = d.pool.RunWithOptions(&dockertest.RunOptions{
			Repository: "postgres",
			Tag:        "13",
			Env: []string{
				fmt.Sprintf("POSTGRES_USER=%s", cfg.PgUser),
				fmt.Sprintf("POSTGRES_PASSWORD=%s", cfg.PgPassword),
				fmt.Sprintf("POSTGRES_DB=%s", cfg.DBName),
			},
			NetworkID: d.network.ID,
		})
		if dbErr != nil {
			log.Printf("Could not start postgres: %v", dbErr)
			return
		}

		postgresPort = pgContainer.GetPort(cfg.PgPort + "/tcp")

		if dbErr = d.pool.Retry(func() error {
			var err error
			postgresDB, err = sql.Open("postgres", fmt.Sprintf(
				"host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
				d.Host, postgresPort, cfg.PgUser, cfg.PgPassword, cfg.DBName,
			))
			if err != nil {
				return err
			}

			return postgresDB.Ping()
		}); dbErr != nil {
			_ = d.pool.Purge(pgContainer)
			log.Printf("Could not connect to postgres: %v", dbErr)
			return
		}

		pgIP := pgContainer.Container.NetworkSettings.Networks[d.network.Name].IPAddress
		migrationContainer, dbErr = d.pool.RunWithOptions(&dockertest.RunOptions{
			Repository: "migrations",
			Tag:        "latest",
			Env: []string{
				fmt.Sprintf("POSTGRES_HOST=%s", pgIP),
				fmt.Sprintf("POSTGRES_PORT=%s", cfg.PgPort),
				fmt.Sprintf("POSTGRES_USER=%s", cfg.PgUser),
				fmt.Sprintf("POSTGRES_PASSWORD=%s", cfg.PgPassword),
				fmt.Sprintf("REFERENDUM_DB_NAME=%s", cfg.DBName),
			},
			Cmd:       []string{"alembic", "upgrade", "head"},
			NetworkID: d.network.ID,
		})
		if dbErr != nil {
			_ = d.pool.Purge(pgContainer)
			log.Printf("Could not start migration container: %v", dbErr)
			return
		}
		defer func() {
			_ = d.pool.Purge(migrationContainer)
		}()

		to := 5 * time.Second
		toCtx, cancel := context.WithTimeout(ctx, to)
		defer cancel()

		// Wait for the migration container to exit
		code, dbErr = d.pool.Client.WaitContainerWithContext(migrationContainer.Container.ID, toCtx)
		if dbErr != nil {
			_ = d.pool.Purge(pgContainer)
			log.Printf("Error waiting for migration container to stop: %v", dbErr)
			return
		} else if code != 0 {
			_ = d.pool.Purge(pgContainer)
			var logBuffer bytes.Buffer
			logErr := d.pool.Client.Logs(docker.LogsOptions{
				Container:    migrationContainer.Container.ID,
				OutputStream: &logBuffer,
				ErrorStream:  &logBuffer,
				Stdout:       true,
				Stderr:       true,
			})
			if logErr == nil {
				log.Printf("DB migration failed with logs: %s", logBuffer.String())
			}
			dbErr = fmt.Errorf("migration container exited with code %d", code)
			return
		}
	})

	if dbErr != nil {
		return nil, dbErr
	}

	log.Printf("Successfully setup postgres DB container on port: %s\n", postgresPort)

	cfg.PgHost = d.Host
	cfg.PgPort = postgresPort

	return &PostgresContainer{
		DB:          postgresDB,
		Port:        postgresPort,
		DBSchema:    cfg.AtpDBSchema,
		pgContainer: pgContainer,
	}, nil
}

// ResetDatabase clears all data, useful between tests
func (pc *PostgresContainer) ResetDatabase() error {
	// Get all tables except postgres system tables
	rows, err := pc.DB.Query(fmt.Sprintf("SELECT tablename FROM pg_tables WHERE schemaname = '%s'", pc.DBSchema))
	if err != nil {
		return err
	}
	defer func() {
		_ = rows.Close()
	}()

	// Disable triggers and truncate each table
	_, err = pc.DB.Exec("SET session_replication_role = 'replica';")
	if err != nil {
		return err
	}

	for rows.Next() {
		var tableName string
		if scanErr := rows.Scan(&tableName); scanErr != nil {
			return scanErr
		}
		_, err = pc.DB.Exec(fmt.Sprintf("TRUNCATE TABLE %s CASCADE;", tableName))
		if err != nil {
			return err
		}
	}

	if rowErr := rows.Err(); err != nil {
		return fmt.Errorf("row iteration failed: %w", rowErr)
	}

	_, err = pc.DB.Exec("SET session_replication_role = 'origin';")
	return err
}

// CleanupPostgres should be called after all tests are done
func (pc *PostgresContainer) CleanupPostgres(d *Docker) {
	if pc.DB != nil {
		_ = pc.DB.Close()
	}

	if pc.pgContainer != nil {
		if err := d.pool.Purge(pc.pgContainer); err != nil {
			log.Printf("Could not purge postgres container: %s", err)
		}
	}

	log.Println("PostgreSQL test resources cleaned up")
}
