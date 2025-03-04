// Contains all environment variables required for initializing the service

package config

import (
	"log"
	"os"
)

func getEnvOrFail(key string) string {
	val := os.Getenv(key)
	if val == "" {
		log.Fatalf("Missing required environment variable: %s", key)
	}

	return val
}

type Config struct {
	PgUser     string
	PgPassword string
	PgHost     string
	PgPort     string
	DBName     string
	SecretKey  []byte
}

func LoadConfigFromEnv() Config {
	config := Config{
		// Database
		PgUser:     getEnvOrFail("POSTGRES_USER"),
		PgPassword: getEnvOrFail("POSTGRES_PASSWORD"),
		PgHost:     getEnvOrFail("POSTGRES_HOST"),
		PgPort:     getEnvOrFail("POSTGRES_PORT"),
		DBName:     getEnvOrFail("REFERENDUM_DB_NAME"),

		// Server
		SecretKey: []byte(getEnvOrFail("SECRET_KEY")),
	}

	return config
}
