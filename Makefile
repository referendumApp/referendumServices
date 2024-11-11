.PHONY: build local pipeline test clean shell logs restart

# Build the Docker images
build:
	docker compose --profile "*" build

# Run the application in local development mode
local:
	docker compose --profile local-data build
	docker compose --profile local-data up

# Run the application in local development mode without the pipeline
empty:
	docker compose --profile local-empty build
	docker compose --profile local-empty up

# Run the tests
pytest:
	docker compose --profile test build
	docker compose --profile test run --rm test

# Clean up Docker resources
clean:
	docker compose down --remove-orphans
	docker system prune -f
	docker volume prune -f

# Start a shell in the app container
shell:
	docker compose --profile local run --rm app sh

# View logs
logs:
	docker compose logs -f

# Rebuild and restart the app in local development mode
restart: clean local

# Run tests and cleanup
test: clean pytest clean
