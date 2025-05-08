//go:build init

package main

import (
	"context"
	"fmt"
	"os"
	"testing"
	"time"

	_ "github.com/lib/pq"
	"github.com/referendumApp/referendumServices/internal/env-config"
	"github.com/referendumApp/referendumServices/testutil"
)

func TestServiceInitialization(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	cfg, err := env.LoadConfig()
	if err != nil {
		t.Fatalf("Failed to load environment variables: %v", err)
	}

	docker, err := testutil.SetupDocker()
	if err != nil {
		t.Fatalf("Failed to setup docker API and network: %v", err)
	}
	defer docker.CleanupDocker()

	pc, err := docker.SetupPostgres(ctx, cfg.DBConfig)
	if err != nil {
		t.Fatalf("Failed to setup postgres container: %v", err)
	}
	defer pc.CleanupPostgres(docker)

	sc, err := docker.SetupS3(ctx)
	if err != nil {
		t.Fatalf("Failed to setup minio container: %v", err)
	}
	defer sc.CleanupS3(docker)
	t.Logf("S3_ENDPOINT_URL: %s\n", os.Getenv("S3_ENDPOINT_URL"))

	kms, err := docker.SetupKMS(ctx, cfg)
	if err != nil {
		t.Fatalf("Failed to setup kms container: %v", err)
	}
	defer kms.CleanupKMS(docker)
	t.Logf("KMS_HOST: %s\n", os.Getenv("KMS_HOST"))

	done := make(chan struct{})

	go func() {
		defer close(done)
		if err := run(ctx, os.Stdout, cfg); err != nil {
			t.Errorf("Failed to start server: %v", err)
		}
	}()
	time.Sleep(1 * time.Second)

	cancel()

	<-done
	fmt.Println("Server shutdown complete")
}
