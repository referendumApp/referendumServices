package common

import (
	"fmt"
	"os"
	"path/filepath"
)

// FindProjectRoot returns project root based on 'go.mod' file location
func FindProjectRoot() (string, error) {
	dir, err := os.Getwd()
	if err != nil {
		return "", err
	}

	// Only return the directory if `go.mod` is found in the filepath
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			if dir == "/" {
				return ".", nil
			}
			return dir, nil
		}

		parent := filepath.Dir(dir)
		if parent == dir {
			return "", fmt.Errorf("could not find project root, no go.mod file found")
		}
		dir = parent
	}
}
