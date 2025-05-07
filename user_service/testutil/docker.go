package testutil

import (
	"log"
	"os"
	"sync"

	"github.com/ory/dockertest/v3"
	"github.com/ory/dockertest/v3/docker"
)

var (
	dockerOnce sync.Once
	pool       *dockertest.Pool
	network    *docker.Network
)

// Docker holds the docker API and network dependencies
type Docker struct {
	pool    *dockertest.Pool
	network *docker.Network
}

// SetupDocker creates a pool and network
func SetupDocker() (*Docker, error) {
	var dockerErr error

	dockerOnce.Do(func() {
		pool, dockerErr = dockertest.NewPool("")
		if dockerErr != nil {
			log.Printf("Could not create docker pool: %s", dockerErr)
			return
		}

		network, dockerErr = pool.Client.CreateNetwork(docker.CreateNetworkOptions{
			Name: "test-network",
		})
		if dockerErr != nil {
			log.Printf("Could not create network: %s", dockerErr)
			return
		}
	})

	if dockerErr != nil {
		return nil, dockerErr
	}

	log.Println("Successfully setup Docker pool and network")

	return &Docker{pool: pool, network: network}, nil
}

// CleanupDocker cleans up test docker network
func (d *Docker) CleanupDocker() {
	if d.network != nil {
		if err := d.pool.Client.RemoveNetwork(d.network.ID); err != nil {
			log.Printf("Could not delete test network: %s", err)
		}
	}

	log.Println("Docker test network removed")
}

func (d *Docker) getLocalDockerHost(ns *docker.NetworkSettings) string {
	if _, err := os.Stat("/.dockerenv"); err == nil {
		return ns.Networks[d.network.Name].IPAddress
		// return "host.docker.internal"
	}

	return "localhost"
}
