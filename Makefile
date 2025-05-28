.PHONY: build local empty pipeline test clean shell logs restart test-api test-pipeline test-user lint build-schema

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

# Run data service tests
pytest-api:
	docker compose --profile test run --rm data-test pytest $(ARGS) api/ common/

pytest-pipeline:
	docker compose --profile test run --rm data-test pytest $(ARGS) pipeline/

# Run user service tests
go-test-user:
	docker compose --profile test run --rm user-test

# Run linting for user service
lint-user:
	cd user_service && golangci-lint run

# Build lexicon schema for user service
build-schema:
	cd user_service && go run ./cmd/lexgen --build-file ./cmd/lexgen/build-config.json "./cmd/lexgen/lexicons/com/referendumapp"

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

# Run all tests with proper cleanup between test suites
test: clean build
	docker compose --profile test run --rm data-test pytest $(ARGS) api/ common/
	docker compose --profile test down --remove-orphans
	docker compose --profile test run --rm data-test pytest $(ARGS) pipeline/
	docker compose --profile test down --remove-orphans
	docker compose --profile test run --rm user-test
	$(MAKE) clean

# Run tests in parallel isolated environments
test-parallel: clean build
	docker compose --profile test -p api-test run --rm data-test pytest $(ARGS) api/ common/ && \
	docker compose --profile test -p api-test down --remove-orphans || \
	(docker compose --profile test -p api-test down --remove-orphans && exit 1)

	docker compose --profile test -p pipeline-test run --rm data-test pytest $(ARGS) pipeline/ && \
	docker compose --profile test -p pipeline-test down --remove-orphans || \
	(docker compose --profile test -p pipeline-test down --remove-orphans && exit 1)

	docker compose --profile test -p user-test run --rm user-test && \
	docker compose --profile test -p user-test down --remove-orphans || \
	(docker compose --profile test -p user-test down --remove-orphans && exit 1)

	$(MAKE) clean

# Run specific test suites with cleanup
test-api: clean build pytest-api clean
test-pipeline: clean build pytest-pipeline clean
test-user: clean build lint-user build-schema go-test-user clean
