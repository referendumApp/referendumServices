# Referendum Services

Backend infrastructure for the Referendum mobile app

## 🚀 Quick Start

1. **Prerequisites**
   - Docker and Docker Compose
   - Python 3.13+
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
   - Localstack Console: http://localhost:4566 
   - Database: localhost:5432 (PostgreSQL)

## 🏗 Architecture

### 1. API Service
- FastAPI application handling all client requests
- Features:
  - JWT-based user authentication and role-based authorization
  - RESTful endpoints for legislative data and user interactions
  - Swagger/OpenAPI documentation

### 2. ETL Pipeline
- Weekly automated data synchronization from Legiscan
- Text processing pipeline

### 3. Infrastructure
- **Database Layer**:
  - PostgreSQL 14+ for structured data
  - RDS for deployed system
- **Storage Layer**:
  - S3 buckets for bill texts and attachments
  - Localstack for local development
- **AWS Deployment**:
  - EC2 for compute resources
  - ECR for container registry
  - ECS for container orchestration
  - CloudWatch for monitoring and logging

## ⚙️ Configuration

### Environment Variables
```bash
# Application Settings
ENVIRONMENT=                # local/dev/prod
LOG_LEVEL=                  # DEBUG/INFO/WARNING/ERROR

# Database Configuration
POSTGRES_HOST=              # Database hostname
POSTGRES_PORT=              # Database port (default: 5432)
POSTGRES_USER=              # Database username
POSTGRES_PASSWORD=          # Database password
REFERENDUM_DB_NAME=         # Main application database name
LEGISCAN_API_DB_NAME=       # Legiscan sync database name

# Authentication
SECRET_KEY=                 # JWT signing key (min 32 chars)
API_ACCESS_TOKEN=           # API gateway access token

# AWS/S3 Configuration
AWS_REGION=                 # AWS region (default: us-east-1)
S3_ACCESS_KEY=              # S3 access key
S3_SECRET_KEY=              # S3 secret key
BILL_TEXT_BUCKET_NAME=      # S3 bucket for bill texts
```

## 🛠 Development

### Testing
```bash
# Run all tests
make test
```

### Local Development Tips
- 

## 🔄 Data Pipeline

ETL pipeline for Legiscan data synchronization and processing.

### Pipeline Stages
1. **Fetch**: Download updates from Legiscan API
2. **Transform**: Process and normalize data
3. **Load**: Update database records to Referendum DB
4. **Text Processing**: Extract and index bill texts

### Manual Execution
```bash
# Local execution with debug logging
make pipeline

# AWS execution with environment selection
gh workflow run run_pipeline.yml -f environment=<environment>
```

## 📦 Deployment

### Environments

| Environment | Config Location | Image Tags | Auto Deploy | Usage |
|-------------|-----------------|------------|-------------|--------|
| Development | `/dev/` in SSM | `dev-${SHA}`, `dev-stable` | On PR merge | Testing & QA |
| Production  | `/prod/` in SSM | `prod-${SHA}`, `prod-stable` | Manual | Live service |

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
