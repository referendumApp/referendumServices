# Referendum Services

## Architecture

The Referendum system consists of the following services:
- **api**: The main FastAPI application service that handles HTTP requests
- **pipeline**: ETL service for processing legislative data
- **db**: PostgreSQL database service for local development
- **local-init**: Service that runs initialization scripts for local development
- **migrations**: Handles database schema updates using Alembic
- **test**: Runs the test suite in an isolated environment

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

The API will be available at:
- Main API: `http://localhost:80`
- API documentation: `http://localhost:80/docs`

### Running Tests

```bash
make test
```

### Stopping the Application and Cleaning the Environment

```bash
make clean
```

## Deployment

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
4. Runs database migrations using Alembic
5. Replaces running image with new build
6. Validates using health check
7. Updates stable tag if successful, rolls back if failed

For detailed information about the CI/CD process, refer to the `.github/workflows/deploy.yml` file in the repository.

#### Deploy Pipeline to AWS
1. Builds and pushes pipeline image to ECR
2. Updates ECS task definition
3. Configures EventBridge rule for weekly execution

### Environments

Both environments run on the same EC2 instance, with different tags and ports:

- **Production**: 
  - Deployed automatically on pushes to the main branch
  - Runs on port 80
  - Uses parameters from `/prod/` in SSM Parameter Store
  - Image tagged as `prod-${SHA}` and `prod-stable`

- **Dev**: 
  - Can be deployed manually using Github Actions workflow dispatch
  - Runs on port 8080
  - Uses parameters from `/dev/` in SSM Parameter Store
  - Image tagged as `dev-${SHA}` and `dev-stable`

### Version Management

- Version numbers are maintained in `version.txt`
- Automatically incremented on main branch pushes
- Commit messages can include:
  - `#major`: Bumps major version (x.0.0)
  - `#minor`: Bumps minor version (0.x.0)
  - Default: Bumps patch version (0.0.x)

### Monitoring and Troubleshooting
- AWS SSO Login: https://d-9a677b7194.awsapps.com/start
