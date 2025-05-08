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
	Host    string
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

	host := getLocalDockerHost(pool.Client)

	return &Docker{pool: pool, network: network, Host: host}, nil
}

// CleanupDocker cleans up test docker network
func (d *Docker) CleanupDocker() {
	var networkName string
	if d.network != nil {
		networkName = d.network.Name
		if err := d.pool.Client.RemoveNetwork(d.network.ID); err != nil {
			log.Printf("Could not delete test network: %s", err)
		}
	}

	log.Printf("Docker test network removed: %s\n", networkName)
}

func getLocalDockerHost(c *docker.Client) string {
	// TODO: This is a workaround for the `host-gateway` mapping bug when running the Docker Engine natively on Linux
	// https://github.com/docker/buildx/issues/1832
	if os.Getenv("CI") == "true" {
		hostIP, err := getHostGatewayIP(c)
		if err == nil && hostIP != "" {
			log.Printf("Docker network host IP found: %s", hostIP)
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

func getHostGatewayIP(c *docker.Client) (string, error) {
	// Get details about the "bridge" network
	network, err := c.NetworkInfo("bridge")
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
