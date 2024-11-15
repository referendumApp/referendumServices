# Referendum Services

Backend infrastructure for the Referendum mobile app, providing APIs and data pipelines for legislative data management and user engagement.

## 🚀 Quick Start

1. **Prerequisites**
   - Docker and Docker Compose
   - Python 3.11+
   - [Referendum AWS Account](https://d-9a677b7194.awsapps.com/start)
   - AWS CLI configured with SSO access

2. **Setup**
   ```bash
   # Clone and setup
   git clone [repository-url]
   cd referendum-services
   cp .env.example .env
   
   # Configure AWS SSO (if not already done)
   aws configure sso
   
   # Start services
   make local  # with sample data including test bills and users
   # OR
   make empty  # clean start without sample data
   ```

3. **Access Points**
   - API: http://localhost:80 (main service endpoint)
   - API Documentation: 
     - Swagger UI: http://localhost:80/docs (interactive API testing)
     - Redoc: http://localhost:80/redoc (detailed API documentation)
   - MinIO Console: http://localhost:9001 (S3-compatible storage interface)
   - Database: localhost:5432 (PostgreSQL)

## 🏗 Architecture

The system follows a microservices architecture with three main components:

### 1. API Service
- FastAPI application handling all client requests
- Features:
  - JWT-based user authentication and role-based authorization
  - RESTful endpoints for bill data and user interactions
  - WebSocket support for real-time updates
  - Rate limiting and request validation
  - Comprehensive logging and monitoring
  - Swagger/OpenAPI documentation

### 2. ETL Pipeline
- Weekly automated data synchronization from Legiscan
  - Bill metadata and status updates
  - Legislator information
  - Committee data
  - Voting records
- Text processing pipeline:
  - PDF extraction and parsing
  - Full-text search indexing
  - Content categorization
  - Storage optimization
- Monitoring and alerting for pipeline failures

### 3. Infrastructure
- **Database Layer**:
  - PostgreSQL 14+ for structured data
  - Materialized views for complex queries
  - Automatic backups and point-in-time recovery
- **Storage Layer**:
  - S3 buckets for bill texts and attachments
  - MinIO for local development
  - Lifecycle policies for cost optimization
- **AWS Deployment**:
  - EC2 for compute resources
  - ECR for container registry
  - ECS for container orchestration
  - Application Load Balancer for traffic distribution
  - CloudWatch for monitoring and logging

## ⚙️ Configuration

### Environment Variables
```bash
# Database Configuration
POSTGRES_HOST=              # Database hostname
POSTGRES_PORT=              # Database port (default: 5432)
POSTGRES_USER=              # Database username
POSTGRES_PASSWORD=          # Database password
REFERENDUM_DB_NAME=         # Main application database name
LEGISCAN_API_DB_NAME=      # Legiscan sync database name

# Authentication
SECRET_KEY=                 # JWT signing key (min 32 chars)
API_ACCESS_TOKEN=           # API gateway access token

# AWS/S3 Configuration
AWS_REGION=                 # AWS region (default: us-west-2)
S3_ACCESS_KEY=             # S3/MinIO access key
S3_SECRET_KEY=             # S3/MinIO secret key
BILL_TEXT_BUCKET_NAME=     # S3 bucket for bill texts

# Application Settings
ENVIRONMENT=                # local/dev/prod
LOG_LEVEL=                 # DEBUG/INFO/WARNING/ERROR
```

## 🛠 Development

### Code Quality
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install and configure pre-commit hooks
pip install pre-commit
pre-commit install

# Manual code formatting
black .
ruff check .
mypy .

# Generate API documentation
make docs
```

### Testing
```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration
make test-e2e

# Clean up test artifacts
make clean
```

### Local Development Tips
- Use `make logs` to follow service logs
- `make shell` opens a Python shell with app context
- `make db-shell` connects to PostgreSQL
- Hot reload is enabled by default
- Set `DEBUG=1` for additional logging

## 🔄 Data Pipeline

Weekly ETL pipeline for Legiscan data synchronization and processing.

### Pipeline Stages
1. **Fetch**: Download updates from Legiscan API
2. **Transform**: Process and normalize data
3. **Load**: Update database records
4. **Process**: Extract and index bill texts
5. **Verify**: Validate data integrity

### Manual Execution
```bash
# Local execution with debug logging
make pipeline

# AWS execution with environment selection
gh workflow run run_pipeline.yml -f environment=<environment>

# Force full refresh
make pipeline-full-refresh
```

## 📦 Deployment

### Environments

| Environment | Port | Config Location | Image Tags | Auto Deploy | Usage |
|-------------|------|-----------------|------------|-------------|--------|
| Development | 8080 | `/dev/` in SSM | `dev-${SHA}`, `dev-stable` | On PR merge | Testing & QA |
| Production  | 80   | `/prod/` in SSM | `prod-${SHA}`, `prod-stable` | Manual | Live service |

### Deployment Steps

1. **Build and Deploy**
   ```bash
   # Automatic deployment on main branch push (prod)
   
   # Manual deployment to dev:
   gh workflow run deploy.yml -f environment=dev
   
   # Manual deployment to prod:
   gh workflow run deploy.yml -f environment=prod
   ```

2. **Database Migration**
   ```bash
   # Apply migrations
   gh workflow run migration.yml \
     -f environment=dev \
     -f operation=upgrade \
     -f version=head
   
   # Rollback if needed
   gh workflow run migration.yml \
     -f environment=dev \
     -f operation=downgrade \
     -f version=-1
   ```

### Monitoring
- CloudWatch dashboards for service metrics
- Automated alerts for:
  - API error rates
  - Pipeline failures
  - Resource utilization
  - Response time thresholds

## 📝 Version Management

- Version format: MAJOR.MINOR.PATCH
- Automatic versioning via commit messages:
  - `#major`: Breaking changes (e.g., API changes, schema updates)
  - `#minor`: New features (backward compatible)
  - Default: Patch updates (bug fixes, minor improvements)
- Release tags are automatically created
- Changelog is generated from commit history

## 🤝 Contributing

1. **Branch Naming**
   - Feature: `feature/<description>`
   - Bugfix: `fix/<description>`
   - Release: `release/v<version>`

2. **Development Process**
   - Create branch from `main`
   - Develop and test locally
   - Ensure all tests pass
   - Update documentation if needed
   - Submit PR for review

3. **Code Standards**
   - Follow PEP 8 style guide
   - Include docstrings for all functions
   - Add type hints
   - Maintain test coverage
   - Pass all linting checks

4. **Review Process**
   - At least one approval required
   - All CI checks must pass
   - No merge conflicts
   - Up-to-date with main branch