.PHONY: build run test clean shell logs restart

# Build the Docker images
build:
	docker compose --profile dev build

# Run the application in local development mode
run: build
	docker compose --profile dev up

# Run the tests
test: build
	docker compose --profile test up --exit-code-from test

# Clean up Docker resources
clean:
	docker compose down --remove-orphans
	docker system prune -f

# Start a shell in the app container
shell:
	docker compose --profile dev run --rm app sh

# View logs
logs:
	docker compose logs -f

# Rebuild and restart the app in local development mode
restart: clean build run
