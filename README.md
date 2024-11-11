# Referendum Services

This repository provides the backend infrastructure for the Referendum mobile app

## Architecture

The system consists of three main components:

1. **API Service**
   - FastAPI application handling all client requests
   - User authentication and authorization
   - Data access and manipulation
   - Real-time engagement features

2. **ETL Pipeline**
   - Weekly data synchronization from Legiscan
   - Bill text extraction and processing
   - Content storage management

3. **Infrastructure**
   - PostgreSQL database
   - S3 storage for bill texts
   - AWS deployment (EC2, ECR, ECS)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Referendum AWS account & AWS CLI
  - AWS SSO Login: https://d-9a677b7194.awsapps.com/start

### Environment Variables

The following environment variables are required:

```bash
# Database Configuration
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_USER=
POSTGRES_PASSWORD=
REFERENDUM_DB_NAME=
LEGISCAN_API_DB_NAME=

# Authentication
SECRET_KEY=
API_ACCESS_TOKEN=

# AWS/S3 Configuration
AWS_REGION=
S3_ACCESS_KEY=
S3_SECRET_KEY=
BILL_TEXT_BUCKET_NAME=

# Application Settings
ENVIRONMENT=  # (local/dev/prod)
LOG_LEVEL=
```

### Local Development

1. **Clone the Repository**
   ```bash
   git clone [repository-url]
   cd referendum-services
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Local Services**
   ```bash
   # Start with sample data
   make local
   
   # Or start services without
   make empty
   ```

4. **Access Local Environment**
   - API: http://localhost:80
   - API Documentation:
     - Swagger: http://localhost:80/docs
     - Redoc: http://localhost:80/redoc
   - MinIO Console: http://localhost:9001

### Running Tests

```bash
# Run all tests
make test

# Clean up after testing
make clean
```

## Data Pipeline

The ETL pipeline runs weekly to synchronize data from Legiscan and process legislative documents.

### Manual Pipeline Execution

```bash
# Run pipeline locally
make pipeline

# Trigger pipeline in AWS
gh workflow run run_pipeline.yml -f environment=<environment>
```

## Deployment

The service supports two deployment environments:

### Development
- Endpoint: Port 8080
- Configuration: `/dev/` in SSM Parameter Store
- Image tags: `dev-${SHA}` and `dev-stable`

### Production
- Endpoint: Port 80
- Configuration: `/prod/` in SSM Parameter Store
- Image tags: `prod-${SHA}` and `prod-stable`

### Deployment Process

1. **Automated Deployment**
   ```bash
   # Triggered automatically on push to main (prod)
   # Or manually via GitHub Actions
   gh workflow run deploy.yml -f environment=dev
   ```

2. **Manual Database Migration**
   ```bash
   gh workflow run migration.yml \
     -f environment=dev \
     -f operation=upgrade \
     -f version=head
   ```

## Development

### Contribution Guidelines

1. Branch naming: `<author>/`
2. Testing: Ensure all tests pass before submitting PR
3. Linting: Code must pass black formatting checks

## 📝 Version Management

- Version numbers: MAJOR.MINOR.PATCH
- Automatic versioning based on commit messages
  - `#major`: Breaking changes
  - `#minor`: New features
  - Default: Patch updates
