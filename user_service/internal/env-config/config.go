// Contains all environment variables required for initializing the service

package env

import (
	"log"
	"os"
	"strconv"
	"time"
)

func getEnvOrFail(key string) string {
	val := os.Getenv(key)
	if val == "" {
		log.Fatalf("Missing required environment variable: %s", key)
	}

	return val
}

func getIntEnv(key string) int {
	val := getEnvOrFail(key)

	valInt, err := strconv.Atoi(val)
	if err != nil {
		log.Fatalf("Failed to convert %s environment variable to int: %v", key, err)
	}

	return valInt
}

// Config contains all required environment variables
type Config struct {
	Environment  string
	PgUser       string
	PgPassword   string
	PgHost       string
	PgPort       string
	DBName       string
	AtpDBSchema  string
	HandleSuffix string
	ServiceUrl   string
	RecoveryKey  string
	KeyDir       string
	CarDir       string
	CarDBSchema  string
	PLCHost      string
	SecretKey    []byte
	MaxConnLife  time.Duration // Maximum connection lifetime
	MaxConnIdle  time.Duration // Maximum connection idle time}
	CarMaxConns  int
	MaxConns     int32 // Maximum number of connections in the pool
	MinConns     int32 // Minimum number of connections in the pool
}

// LoadConfigFromEnv initializes 'Config' struct
func LoadConfigFromEnv() *Config {
	log.Println("Loading runtime env vars")

	config := Config{
		Environment: getEnvOrFail("ENVIRONMENT"),
		// Database
		PgUser:     getEnvOrFail("POSTGRES_USER"),
		PgPassword: getEnvOrFail("POSTGRES_PASSWORD"),
		PgHost:     getEnvOrFail("POSTGRES_HOST"),
		PgPort:     getEnvOrFail("POSTGRES_PORT"),
		DBName:     getEnvOrFail("REFERENDUM_DB_NAME"),

		// Database pool settings
		MaxConns:    10,
		MinConns:    2,
		MaxConnLife: time.Hour,
		MaxConnIdle: time.Minute * 30,

		// Server
		SecretKey: []byte(getEnvOrFail("SECRET_KEY")),

		// ATP
		HandleSuffix: getEnvOrFail("HANDLE_SUFFIX"),
		ServiceUrl:   getEnvOrFail("USER_SERVICE_URL"),
		AtpDBSchema:  getEnvOrFail("ATP_DB_SCHEMA"),
		RecoveryKey:  getEnvOrFail("PDS_RECOVERY_DID_KEY"),
		KeyDir:       getEnvOrFail("KEYSTORE_DIR"),

		// Carstore
		CarDir:      getEnvOrFail("CARSTORE_DIR"),
		CarDBSchema: getEnvOrFail("CARSTORE_DB_SCHEMA"),
		CarMaxConns: getIntEnv("MAX_CARSTORE_CONNECTIONS"),

		// PLC
		PLCHost: getEnvOrFail("PLC_HOST"),
	}

	log.Println("Successfully loaded env vars!")

	return &config
}
