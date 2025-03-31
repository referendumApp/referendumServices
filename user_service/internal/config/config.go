// Contains all environment variables required for initializing the service

package config

import (
	"log/slog"
	"os"
	"strconv"
	"time"
)

func getEnvOrFail(log *slog.Logger, key string) string {
	val := os.Getenv(key)
	if val == "" {
		log.Warn("Missing required environment variable", "key", key)
	}

	return val
}

func getIntEnv(log *slog.Logger, key string) int {
	val := getEnvOrFail(log, key)

	valInt, err := strconv.Atoi(val)
	if err != nil {
		log.Error("Failed to convert environment variable to int", "key", key, "error", err)
		os.Exit(1)
	}

	return valInt
}

type Config struct {
	PgUser       string
	PgPassword   string
	PgHost       string
	PgPort       string
	DBName       string
	HandleSuffix string
	ServiceUrl   string
	CarDir       string
	CarDBName    string
	PLCHost      string
	SecretKey    []byte
	MaxConnLife  time.Duration // Maximum connection lifetime
	MaxConnIdle  time.Duration // Maximum connection idle time}
	CarMaxConns  int
	MaxConns     int32 // Maximum number of connections in the pool
	MinConns     int32 // Minimum number of connections in the pool
}

func LoadConfigFromEnv(log *slog.Logger) Config {
	log.Info("Loading runtime env vars")

	config := Config{
		// Database
		PgUser:     getEnvOrFail(log, "POSTGRES_USER"),
		PgPassword: getEnvOrFail(log, "POSTGRES_PASSWORD"),
		PgHost:     getEnvOrFail(log, "POSTGRES_HOST"),
		PgPort:     getEnvOrFail(log, "POSTGRES_PORT"),
		DBName:     getEnvOrFail(log, "REFERENDUM_DB_NAME"),

		// Database pool settings
		MaxConns:    10,
		MinConns:    2,
		MaxConnLife: time.Hour,
		MaxConnIdle: time.Minute * 30,

		// Server
		SecretKey: []byte(getEnvOrFail(log, "SECRET_KEY")),

		// ATP
		HandleSuffix: getEnvOrFail(log, "ATP_HANDLE_SUFFIX"),
		ServiceUrl:   getEnvOrFail(log, "ATP_SERVICE_URL"),

		// Carstore
		CarDir:      getEnvOrFail(log, "CARSTORE_DIR"),
		CarDBName:   getEnvOrFail(log, "CARSTORE_DB_NAME"),
		CarMaxConns: getIntEnv(log, "MAX_CARSTORE_CONNECTIONS"),

		// PLC
		PLCHost: getEnvOrFail(log, "PLC_HOST"),
	}

	log.Info("Successfully loaded env vars!")

	return config
}
