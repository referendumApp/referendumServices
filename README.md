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
* AWS CLI configured with appropriate permissions

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

### Environment Variables

Environment-specific variables are stored in AWS Systems Manager Parameter Store. They are organized under paths:
- Production: `/prod/`
- Test: `/dev/`

Required parameters for each environment:
- POSTGRES_HOST
- POSTGRES_PORT
- POSTGRES_USER
- POSTGRES_PASSWORD
- REFERENDUM_DB_NAME
- LEGISCAN_API_DB_NAME

### Deployment Workflows
 
#### Deploy API to AWS
Triggered on push to main or manually via workflow dispatch.
1. Builds the API Docker image using environment variables from SSM Parameter Store
1. Pushes the image to Amazon ECR at referendum/api
1. Uses AWS Systems Manager to pull image to EC2 instance
1. Replaces running image with new build
1. Validates using health check

For detailed information about the CI/CD process, refer to the `.github/workflows/deploy.yml` file in the repository.

### Environments

Both environments are run on the same EC2 server, with different tags and ports:

- **Production**: 
  - Deployed automatically on pushes to the main branch
  - Runs on port 80
  - Uses parameters from `/prod/` in SSM Parameter Store

- **Dev**: 
  - Can be deployed manually using Github Actions workflow dispatch
  - Runs on port 8080
  - Uses parameters from `/dev/` in SSM Parameter Store

