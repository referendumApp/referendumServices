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
- Test: `/test/`

Required parameters for each environment:
- DATABASE_URL
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_DB

### Deployment Process

1. GitHub Actions workflow is triggered on push to main or manually via workflow dispatch.
2. The workflow builds the Docker image and pushes it to Amazon ECR.
3. The image is then deployed to an EC2 instance using AWS Systems Manager Run Command.
4. Environment variables are fetched from SSM Parameter Store during deployment.

### Environments

Both environments are run on the same EC2 server, with different tags and ports:

- **Production**: 
  - Deployed automatically on pushes to the main branch
  - Runs on port 80
  - Uses parameters from `/prod/` in SSM Parameter Store

- **Test**: 
  - Can be deployed manually using Github Actions workflow dispatch
  - Runs on port 8080
  - Uses parameters from `/test/` in SSM Parameter Store

### AWS Setup Requirements

1. EC2 instance with Docker installed and appropriate IAM role attached.
2. IAM role for EC2 should have permissions to:
   - Pull images from ECR
   - Read parameters from SSM Parameter Store
3. SSM Parameter Store should contain the required environment variables for both prod and test environments.
4. GitHub repository should have AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY secrets set for deployment.

## Continuous Integration

GitHub Actions is used for CI/CD. The workflow includes:
- Building and pushing Docker images to ECR
- Deploying to EC2
- Running health checks post-deployment
- Automatic rollback in case of deployment failure

For detailed information about the CI/CD process, refer to the `.github/workflows/deploy.yml` file in the repository.
