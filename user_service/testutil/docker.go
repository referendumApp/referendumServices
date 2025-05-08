package testutil

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
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

func (d *Docker) getLocalDockerHost() string {
	if os.Getenv("CI") == "true" {
		hostIP, err := d.getHostGatewayIP()
		if err == nil && hostIP != "" {
			log.Printf("Host IP found: %s", hostIP)
			return hostIP
		}

		defaultIP, err := getDefaultRouteIP()
		if err == nil && defaultIP != "" {
			log.Printf("Default IP found: %s", defaultIP)
			return defaultIP
		}
	}

	if _, err := os.Stat("/.dockerenv"); err == nil {
		return "host.docker.internal"
	}

	return "localhost"
}

func (d *Docker) getHostGatewayIP() (string, error) {
	// Get details about the "bridge" network
	network, err := d.pool.Client.NetworkInfo("bridge")
	if err != nil {
		return "", fmt.Errorf("failed to get bridge network info: %w", err)
	}

	// Extract the gateway IP address
	if len(network.IPAM.Config) > 0 {
		return network.IPAM.Config[0].Gateway, nil
	}

	return "", fmt.Errorf("no gateway found for bridge network")
}

func getDefaultRouteIP() (string, error) {
	cmd := exec.Command("sh", "-c", "ip route | grep default | awk '{print $3}'")
	out, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(out)), nil
}
