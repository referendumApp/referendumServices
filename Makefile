.PHONY: build run test clean

# Build the Docker images
build:
	docker compose build

# Run the application
run: build
	docker compose up app

# Run the tests
test: build
	docker compose run --rm test

# Clean up Docker resources
clean:
	docker compose down --remove-orphans
	docker system prune -f

# Start a shell in the app container
shell:
	docker compose run --rm app sh

# View logs
logs:
	docker compose logs -f

# Rebuild and restart the app
restart: clean build run
