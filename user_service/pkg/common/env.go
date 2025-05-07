package common

import (
	"fmt"
	"os"
	"strconv"
)

// GetEnvOrFail returns environment variable or exits the program
func GetEnvOrFail(key string) (string, error) {
	val := os.Getenv(key)
	if val == "" {
		return "", fmt.Errorf("missing required environment variable: %s", key)
	}

	return val, nil
}

// GetIntEnv returns int environment variable or exits the program
func GetIntEnv(key string) (int, error) {
	val, err := GetEnvOrFail(key)
	if err != nil {
		return 0, err
	}

	valInt, err := strconv.Atoi(val)
	if err != nil {
		return 0, fmt.Errorf("failed to convert %s environment variable to int: %w", key, err)
	}

	return valInt, nil
}
