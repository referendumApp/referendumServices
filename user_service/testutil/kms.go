package testutil

import (
	"context"
	"fmt"
	"log"
	"os"
	"sync"

	_ "github.com/lib/pq"
	"github.com/ory/dockertest/v3"
	"github.com/ory/dockertest/v3/docker"
	"github.com/referendumApp/referendumServices/internal/env-config"
	"github.com/referendumApp/referendumServices/pkg/common"
)

var kmsOnce sync.Once

// KMSContainer holds information about the local-kms docker container
type KMSContainer struct {
	Port         string
	kmsContainer *dockertest.Resource
}

// SetupKMS creates a local-kms container
func (d *Docker) SetupKMS(ctx context.Context, cfg *env.Config) (*KMSContainer, error) {
	var (
		initContainer *dockertest.Resource
		kmsContainer  *dockertest.Resource
		seedContent   []byte
		kmsPort       string
		kmsErr        error
	)

	region, err := common.GetEnvOrFail("AWS_REGION")
	if err != nil {
		return nil, err
	}
	acctId, err := common.GetEnvOrFail("KMS_ACCOUNT_ID")
	if err != nil {
		return nil, err
	}
	expPort, err := common.GetEnvOrFail("KMS_PORT")
	if err != nil {
		return nil, err
	}
	pwd, err := common.FindProjectRoot()
	if err != nil {
		return nil, err
	}

	kmsOnce.Do(func() {
		// Create a Docker volume
		volumeName := "kms-seed-volume"
		if _, kmsErr = d.pool.Client.CreateVolume(docker.CreateVolumeOptions{
			Name: volumeName,
		}); kmsErr != nil {
			log.Printf("Failed to create volume: %v", kmsErr)
			return
		}

		// Read the seed file content from your container
		seedContent, kmsErr = os.ReadFile(pwd + "/kms_seed.yaml")
		if kmsErr != nil {
			log.Printf("Failed to read seed file: %v", kmsErr)
			return
		}

		initContainer, kmsErr = d.pool.RunWithOptions(&dockertest.RunOptions{
			Repository: "alpine",
			Tag:        "latest",
			Cmd: []string{
				"sh", "-c",
				"mkdir -p /data && echo '" + string(seedContent) + "' > /data/seed.yaml",
			},
			Mounts: []string{
				fmt.Sprintf("%s:/data", volumeName),
			},
		})
		if kmsErr != nil {
			log.Printf("Failed to run init container: %v", err)
			return
		}
		defer func() {
			_ = d.pool.Purge(initContainer)
		}()

		kmsContainer, kmsErr = d.pool.RunWithOptions(&dockertest.RunOptions{
			Repository: "kng93/local-kms",
			Tag:        "latest",
			Env: []string{
				fmt.Sprintf("KMS_REGION=%s", region),
				fmt.Sprintf("KMS_ACCOUNT_ID=%s", acctId),
				fmt.Sprintf("PORT=%s", expPort),
			},
			ExposedPorts: []string{expPort + "/tcp"},
			Mounts:       []string{volumeName + ":/init"},
			NetworkID:    d.network.ID,
		})
		if kmsErr != nil {
			log.Printf("Could not start KMS container: %v", kmsErr)
			return
		}

		kmsPort = kmsContainer.GetPort(expPort + "/tcp")
		kmsIP := kmsContainer.Container.NetworkSettings.Networks[d.network.Name].IPAddress

		if kmsErr = d.pool.Retry(func() error {
			if ec, err := kmsContainer.Exec(
				[]string{
					"curl",
					"-f",
					fmt.Sprintf("http://%s:%s", kmsIP, expPort),
					"-H",
					"X-Amz-Target: TrentService.ListKeys",
					"-H",
					"Content-Type: application/x-amz-json-1.1",
					"-d",
					"{}",
				},
				dockertest.ExecOptions{},
			); err != nil {
				return err
			} else if ec != 0 {
				return fmt.Errorf("KMS container healthcheck exited with code: %d", ec)
			}

			return nil
		}); kmsErr != nil {
			_ = d.pool.Purge(kmsContainer)
			log.Printf("KMS healthcheck failed: %v", kmsErr)
			return
		}
	})

	if kmsErr != nil {
		return nil, kmsErr
	}

	log.Printf("Successfully setup KMS container on port: %s\n", kmsPort)

	if err := os.Setenv("KMS_HOST", d.Host+":"+kmsPort); err != nil {
		return nil, fmt.Errorf("failed to set KMS_HOST environment variable: %w", err)
	}

	return &KMSContainer{Port: kmsPort, kmsContainer: kmsContainer}, nil
}

// CleanupKMS should be called after all tests are done
func (kc *KMSContainer) CleanupKMS(d *Docker) {
	// Remove containers
	if kc.kmsContainer != nil {
		if err := d.pool.Purge(kc.kmsContainer); err != nil {
			log.Printf("Could not purge KMS container: %s", err)
		}
	}

	log.Println("KMS test resources cleaned up")
}
