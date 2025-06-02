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

var s3Once sync.Once

// S3Container holds information about the LocalStack docker container
type S3Container struct {
	Port        string
	s3Container *dockertest.Resource
}

// SetupS3 creates a LocalStack container with S3 service
func (d *Docker) SetupS3(ctx context.Context) (*S3Container, error) {
	var (
		s3Container *dockertest.Resource
		s3Port      string
		s3Err       error
	)

	id, err := common.GetEnvOrFail("AWS_ACCESS_KEY_ID")
	if err != nil {
		return nil, err
	}
	secret, err := common.GetEnvOrFail("AWS_SECRET_ACCESS_KEY")
	if err != nil {
		return nil, err
	}
	expPort, err := common.GetEnvOrFail("LOCALSTACK_PORT")
	if err != nil {
		return nil, err
	}

	s3Once.Do(func() {
		s3Container, s3Err = d.pool.RunWithOptions(&dockertest.RunOptions{
			Repository: "localstack/localstack",
			Tag:        "3.0",
			Env: []string{
				fmt.Sprintf("AWS_ACCESS_KEY_ID=%s", id),
				fmt.Sprintf("AWS_SECRET_ACCESS_KEY=%s", secret),
				"SERVICES=s3,secretsmanager",
				"AWS_DEFAULT_REGION=us-east-1",
			},
			ExposedPorts: []string{expPort + "/tcp"},
			NetworkID:    d.network.ID,
		})
		if s3Err != nil {
			log.Printf("Could not start S3 container: %v", s3Err)
			return
		}

		s3Port = s3Container.GetPort(expPort + "/tcp")
		s3IP := s3Container.Container.NetworkSettings.Networks[d.network.Name].IPAddress

		if s3Err = d.pool.Retry(func() error {
			if ec, err := s3Container.Exec(
				[]string{"curl", "-f", fmt.Sprintf("http://%s:4566/_localstack/health", s3IP)},
				dockertest.ExecOptions{},
			); err != nil {
				return err
			} else if ec != 0 {
				return fmt.Errorf("S3 container healthcheck exited with code: %d", ec)
			}

			return nil
		}); s3Err != nil {
			_ = d.pool.Purge(s3Container)
			log.Printf("S3 healthcheck failed: %v", s3Err)
			return
		}
	})

	if s3Err != nil {
		return nil, s3Err
	}

	log.Printf("Successfully setup S3 container on port: %s\n", s3Port)

	if err := os.Setenv("S3_ENDPOINT_URL", "http://"+d.Host+":"+s3Port); err != nil {
		return nil, fmt.Errorf("failed to set S3_ENDPOINT_URL environment variable: %w", err)
	}

	return &S3Container{Port: s3Port, s3Container: s3Container}, nil
}

// CleanupS3 should be called after all tests are done
func (sc *S3Container) CleanupS3(d *Docker) {
	if sc.s3Container != nil {
		if err := d.pool.Purge(sc.s3Container); err != nil {
			log.Printf("Could not purge Localstack container: %s", err)
		}
	}

	log.Println("S3 test resources cleaned up")
}
