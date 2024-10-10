# Referendum Services

## Architecture

The Referendum system consists of the following services:
- **app**: The main application service that runs the API
- **db**: PostgreSQL database service for local development
- **local-init**: A service that runs initialization scripts for local development
- **test**: A service that runs the test suite in an isolated environment

## Prerequisites

- Python 3.11 or later
- Docker and Docker Compose
- AWS CLI configured with appropriate permissions

## Local Development

### Building the Docker Images

```bash
make build
```

### Running the API Locally

```bash
make local
```

The API will be available at `http://localhost:80` (API documentation at `http://localhost:80/docs`)

### Stopping the Application and Cleaning the Environment

```bash
make clean
```

### Running the Pipeline Locally

```bash
make pipeline
```

### Running Tests

```bash
make test
```

## Deployment

The API image is built with GitHub Actions, pushed to Amazon ECR, and then deployed on an EC2 server.

### Environment Variables

Both applications require the following parameters for each environment:
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `REFERENDUM_DB_NAME`

The pipeline requires:
- `LEGISCAN_API_DB_NAME`

The API requires:
- `SECRET_KEY`
- `API_ACCESS_TOKEN`

#### Variable Storage

- Environment-specific variables are stored in AWS Systems Manager Parameter Store:
  - Production: `/prod/`
  - Test: `/dev/`
- Secrets are stored in AWS Secrets Manager and are integrated into the deployed images as part of the deployment pipeline.

### Deployment Workflow

#### Deploy API to AWS
Triggered on push to main or manually via workflow dispatch.

1. Builds the API Docker image using environment variables from SSM Parameter Store
2. Pushes the image to Amazon ECR at `referendum/api`
3. Uses AWS Systems Manager to pull image to EC2 instance
4. Replaces running image with new build
5. Validates using health check

For detailed information about the CI/CD process, refer to the `.github/workflows/deploy.yml` file in the repository.

### Environments

Both environments run on the same EC2 server, with different tags and ports:

- **Production**: 
  - Deployed automatically on pushes to the main branch
  - Runs on port 80
  - Uses parameters from `/prod/` in SSM Parameter Store

- **Dev**: 
  - Can be deployed manually using Github Actions workflow dispatch
  - Runs on port 8080
  - Uses parameters from `/dev/` in SSM Parameter Store
