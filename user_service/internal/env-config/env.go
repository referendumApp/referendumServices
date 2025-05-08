// Contains all environment variables required for initializing the service

package env

import (
	"log"
	"time"

	"github.com/referendumApp/referendumServices/pkg/common"
)

type DBConfig struct {
	PgUser      string
	PgPassword  string
	PgHost      string
	PgPort      string
	DBName      string
	AtpDBSchema string
	CarDBSchema string
	MaxConnLife time.Duration // Maximum connection lifetime
	MaxConnIdle time.Duration // Maximum connection idle time}
	MaxConns    int32         // Maximum number of connections in the pool
	MinConns    int32         // Minimum number of connections in the pool
}

// Config contains all required environment variables
type Config struct {
	DBConfig     *DBConfig
	Env          string
	HandleSuffix string
	ServiceUrl   string
	RecoveryKey  string
	KeyDir       string
	CarDir       string
	PLCHost      string
	SecretKey    []byte
	CarMaxConns  int
}

// LoadConfig initializes 'Config' struct
func LoadConfig() (*Config, error) {
	log.Println("Loading runtime env vars")

	dbUser, err := common.GetEnvOrFail("POSTGRES_USER")
	if err != nil {
		return nil, err
	}
	dbPw, err := common.GetEnvOrFail("POSTGRES_PASSWORD")
	if err != nil {
		return nil, err
	}
	dbHost, err := common.GetEnvOrFail("POSTGRES_HOST")
	if err != nil {
		return nil, err
	}
	dbPort, err := common.GetEnvOrFail("POSTGRES_PORT")
	if err != nil {
		return nil, err
	}
	dbName, err := common.GetEnvOrFail("REFERENDUM_DB_NAME")
	if err != nil {
		return nil, err
	}
	atpSchema, err := common.GetEnvOrFail("ATP_DB_SCHEMA")
	if err != nil {
		return nil, err
	}
	carSchema, err := common.GetEnvOrFail("CARSTORE_DB_SCHEMA")
	if err != nil {
		return nil, err
	}

	dbConfig := &DBConfig{
		PgUser:      dbUser,
		PgPassword:  dbPw,
		PgHost:      dbHost,
		PgPort:      dbPort,
		DBName:      dbName,
		AtpDBSchema: atpSchema,
		CarDBSchema: carSchema,
		MaxConns:    10,
		MinConns:    2,
		MaxConnLife: time.Hour,
		MaxConnIdle: time.Minute * 30,
	}

	environment, err := common.GetEnvOrFail("ENVIRONMENT")
	if err != nil {
		return nil, err
	}
	skey, err := common.GetEnvOrFail("SECRET_KEY")
	if err != nil {
		return nil, err
	}
	suf, err := common.GetEnvOrFail("HANDLE_SUFFIX")
	if err != nil {
		return nil, err
	}
	url, err := common.GetEnvOrFail("USER_SERVICE_URL")
	if err != nil {
		return nil, err
	}
	rkey, err := common.GetEnvOrFail("PDS_RECOVERY_DID_KEY")
	if err != nil {
		return nil, err
	}
	kd, err := common.GetEnvOrFail("KEYSTORE_DIR")
	if err != nil {
		return nil, err
	}
	cd, err := common.GetEnvOrFail("CARSTORE_DIR")
	if err != nil {
		return nil, err
	}
	conn, err := common.GetIntEnv("MAX_CARSTORE_CONNECTIONS")
	if err != nil {
		return nil, err
	}
	ph, err := common.GetEnvOrFail("PLC_HOST")
	if err != nil {
		return nil, err
	}

	config := &Config{
		DBConfig: dbConfig,
		Env:      environment,

		// Server
		SecretKey: []byte(skey),

		// ATP
		HandleSuffix: suf,
		ServiceUrl:   url,
		RecoveryKey:  rkey,
		KeyDir:       kd,

		// Carstore
		CarDir:      cd,
		CarMaxConns: conn,

		// PLC
		PLCHost: ph,
	}

	log.Println("Successfully loaded env vars!")

	return config, nil
}
