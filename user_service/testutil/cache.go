package testutil

import (
	"context"
	"log"
	"sync"

	_ "github.com/lib/pq"
	"github.com/ory/dockertest/v3"
	"github.com/ory/dockertest/v3/docker"
	"github.com/referendumApp/referendumServices/internal/env-config"
	"github.com/referendumApp/referendumServices/pkg/common"
)

var cacheOnce sync.Once

// CacheContainer holds information about the local-cache docker container
type CacheContainer struct {
	Port           string
	cacheContainer *dockertest.Resource
}

// SetupCache creates a local-cache container
func (d *Docker) SetupCache(ctx context.Context, cfg *env.Config) (*CacheContainer, error) {
	var (
		cacheContainer *dockertest.Resource
		cachePort      string
		cacheErr       error
	)

	expPort, err := common.GetEnvOrFail("CACHE_PORT")
	if err != nil {
		return nil, err
	}

	cacheOnce.Do(func() {
		cacheContainer, cacheErr = d.pool.RunWithOptions(&dockertest.RunOptions{
			Repository:   "docker.dragonflydb.io/dragonflydb/dragonfly",
			Tag:          "latest",
			ExposedPorts: []string{expPort + "/tcp"},
			Cmd:          []string{"dragonfly", "--cache_mode=true"},
			NetworkID:    d.network.ID,
		}, func(config *docker.HostConfig) {
			config.Ulimits = []docker.ULimit{
				{
					Name: "memlock",
					Soft: -1,
					Hard: -1,
				},
			}
		})
		if cacheErr != nil {
			log.Printf("Could not start cache container: %v", cacheErr)
			return
		}

		cachePort = cacheContainer.GetPort(expPort + "/tcp")
	})

	if cacheErr != nil {
		return nil, cacheErr
	}

	log.Printf("Successfully setup cache container on port: %s\n", cachePort)

	cfg.CacheHost = d.Host + ":" + cachePort

	return &CacheContainer{Port: cachePort, cacheContainer: cacheContainer}, nil
}

// CleanupCache should be called after all tests are done
func (c *CacheContainer) CleanupCache(d *Docker) {
	if c.cacheContainer != nil {
		if err := d.pool.Purge(c.cacheContainer); err != nil {
			log.Printf("Could not purge cache container: %s", err)
		}
	}

	log.Println("Cache test resources cleaned up")
}
