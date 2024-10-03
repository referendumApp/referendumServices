.PHONY: build api pipeline test clean shell logs restart

# Build the Docker images
build:
	docker compose --profile "*" build

# Run the application in local development mode
api:
	docker compose --profile dev build
	docker compose --profile dev up

# Run the pipeline in local development mode
pipeline:
	docker compose --profile pipeline --profile dev build
	docker compose --profile pipeline --profile dev up

# Run the tests
test:
	docker compose --profile test build
	docker compose --profile test run --rm test

# Clean up Docker resources
clean:
	docker compose down --remove-orphans
	docker system prune -f
	docker volume prune -f

# Start a shell in the app container
shell:
	docker compose --profile dev run --rm app sh

# View logs
logs:
	docker compose logs -f

# Rebuild and restart the app in local development mode
restart: clean build api
