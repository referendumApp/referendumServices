#!/bin/bash
set -e

echo "Secrets Manager initialization starting..."

# Use localhost since we're running inside the LocalStack container
ENDPOINT="http://localhost:4566"

echo "Waiting for services to be ready..."
for i in {1..30}; do
    if curl -s "$ENDPOINT/_localstack/health" | grep -q '"secretsmanager": "available"'; then
        echo "secretsmanager service is available!"
        break
    fi
    echo "Attempt $i: Waiting for secretsmanager service..."
    sleep 2
done

echo "Creating Secrets Manager secret..."
SECRET_VALUE='{"apiKey":"TEST_API_KEY"}'

aws --endpoint-url="$ENDPOINT" \
    --region=us-east-1 \
    secretsmanager create-secret \
    --name "SYSTEM_USER_SECRET_NAME" \
    --description "System API key for referendum app authentication" \
    --secret-string "$SECRET_VALUE"

echo "LocalStack initialization complete!"
