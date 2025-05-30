package testutil

import (
	"context"
	"fmt"
	"log"
	"os"
	"sync"

	_ "github.com/lib/pq"
	"github.com/ory/dockertest/v3"
	"github.com/referendumApp/referendumServices/pkg/common"
)

var (
	localstackOnce      sync.Once
	localstackContainer *dockertest.Resource
	localstackPort      string
)

// LocalStackContainer holds information about the LocalStack docker container
type LocalStackContainer struct {
	Port                string
	localstackContainer *dockertest.Resource
}

// SetupLocalStack creates a LocalStack container with S3 and SecretsManager services
func (d *Docker) SetupLocalStack(ctx context.Context) (*LocalStackContainer, error) {
	var localstackErr error

	id, err := common.GetEnvOrFail("AWS_ACCESS_KEY_ID")
	if err != nil {
		return nil, err
	}

	secret, err := common.GetEnvOrFail("AWS_SECRET_ACCESS_KEY")
	if err != nil {
		return nil, err
	}

	localstackOnce.Do(func() {
		localstackContainer, localstackErr = d.pool.RunWithOptions(&dockertest.RunOptions{
			Repository: "localstack/localstack",
			Tag:        "3.0",
			Env: []string{
				fmt.Sprintf("AWS_ACCESS_KEY_ID=%s", id),
				fmt.Sprintf("AWS_SECRET_ACCESS_KEY=%s", secret),
				"SERVICES=s3,secretsmanager",
				"AWS_DEFAULT_REGION=us-east-1",
			},
			ExposedPorts: []string{"4566/tcp"},
			NetworkID:    d.network.ID,
		})
		if localstackErr != nil {
			log.Printf("Could not start LocalStack container: %v", localstackErr)
			return
		}

		localstackPort = localstackContainer.GetPort("4566/tcp")
		localstackIP := localstackContainer.Container.NetworkSettings.Networks[d.network.Name].IPAddress

		if localstackErr = d.pool.Retry(func() error {
			if ec, err := localstackContainer.Exec(
				[]string{"curl", "-f", fmt.Sprintf("http://%s:4566/_localstack/health", localstackIP)},
				dockertest.ExecOptions{},
			); err != nil {
				return err
			} else if ec != 0 {
				return fmt.Errorf("LocalStack container healthcheck exited with code: %d", ec)
			}
			return nil
		}); localstackErr != nil {
			_ = d.pool.Purge(localstackContainer)
			log.Printf("LocalStack healthcheck failed: %v", localstackErr)
			return
		}

		// Setup SecretsManager after container is healthy
		if localstackErr = d.setupSecretsManager(); localstackErr != nil {
			_ = d.pool.Purge(localstackContainer)
			log.Printf("SecretsManager setup failed: %v", localstackErr)
			return
		}
	})

	if localstackErr != nil {
		return nil, localstackErr
	}

	log.Printf("Successfully setup LocalStack container on port: %s\n", localstackPort)

	// Set environment variables for both S3 and SecretsManager
	endpointURL := "http://" + d.Host + ":" + localstackPort
	if err := os.Setenv("S3_ENDPOINT_URL", endpointURL); err != nil {
		return nil, fmt.Errorf("failed to set S3_ENDPOINT_URL environment variable: %w", err)
	}
	if err := os.Setenv("SECRETSMANAGER_ENDPOINT_URL", endpointURL); err != nil {
		return nil, fmt.Errorf("failed to set SECRETS_MANAGER_ENDPOINT environment variable: %w", err)
	}

	return &LocalStackContainer{Port: localstackPort, localstackContainer: localstackContainer}, nil
}

// setupSecretsManager creates the API key secret in SecretsManager
func (d *Docker) setupSecretsManager() error {
	log.Println("Creating API key secret for system authentication...")

	// Create the secret in Secrets Manager
	secretValue := `{"apiKey":"TEST_API_KEY"}` // #nosec G101 -- This is a test credential

	exitCode, err := localstackContainer.Exec(
		[]string{
			"aws", "--endpoint-url=http://localhost:4566",
			"--region=us-east-1",
			"secretsmanager", "create-secret",
			"--name", "API_KEY_SECRET_KEY",
			"--description", "System API key for referendum app authentication",
			"--secret-string", secretValue,
		},
		dockertest.ExecOptions{},
	)

	if err != nil {
		return fmt.Errorf("failed to execute secretsmanager create-secret command: %w", err)
	}

	if exitCode != 0 {
		return fmt.Errorf("secretsmanager create-secret command exited with code: %d", exitCode)
	}

	log.Println("Successfully created API_KEY_SECRET_KEY in SecretsManager")
	return nil
}

// CleanupLocalStack should be called after all tests are done
func (lsc *LocalStackContainer) CleanupLocalStack(d *Docker) {
	if lsc.localstackContainer != nil {
		if err := d.pool.Purge(lsc.localstackContainer); err != nil {
			log.Printf("Could not purge LocalStack container: %s", err)
		}
	}
	log.Println("LocalStack test resources cleaned up")
}
