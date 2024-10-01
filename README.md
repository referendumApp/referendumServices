# Referendum Services

## Architecture

The Referendum system consists of the following services:
- app: The application service that runs the API
- db: PostgreSQL database service for local development
- local-init: A service that runs initialization scripts for local development
- test: A service which runs the test suite in an isolated environment

## Prerequisites
* Python 3.9 or later
* Docker and Docker Compose


## Usage

Build the Docker images:
   ```
   make build
   ```

### Running Locally

To start the application, run:

```
make run
```

The API will be available at `http://localhost:80` (API documentation at `http://localhost:80/docs`)

To stop the application, use:

```
make clean
```

### Running Tests

To run the test suite, use:

```
make test
```

## Deployment

The API image is built with GitHub Actions, pushed to ECR, and then deployed on an EC2 server

### Environments

Both environments are run on the same server, with different tags and ports

- **Production**: Deployed automatically on pushes to the main branch, runs on port 80
- **Test**: Can be deployed manually using Github Actions workflow dispatch, runs on port 8080
