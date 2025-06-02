#!/bin/bash
# Create this file as: ./localstack-init/init.sh

set -e

echo "Waiting for LocalStack to be ready..."
until curl -s http://localstack:4566/_localstack/health | grep -q '"s3": "available"'; do
    echo "Waiting for S3 service..."
    sleep 2
done

echo "LocalStack is ready. Creating S3 bucket..."

# Create the bucket
aws --endpoint-url=http://localstack:4566 \
    --region=us-east-1 \
    s3 mb s3://bill-texts

echo "S3 bucket created successfully"

# Set bucket policy for public read
aws --endpoint-url=http://localstack:4566 \
    --region=us-east-1 \
    s3api put-bucket-policy \
    --bucket bill-texts \
    --policy '{
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::bill-texts/*"
        }]
    }'

echo "Bucket policy set successfully"

# Verify bucket exists
aws --endpoint-url=http://localstack:4566 \
    --region=us-east-1 \
    s3 ls s3://bill-texts

echo "LocalStack initialization complete!"

# Setup Secrets Manager
echo "Creating API key secret for system authentication..."

# Create the secret in Secrets Manager
SECRET_VALUE='{"apiKey":"TEST_API_KEY"}'

aws --endpoint-url=http://localstack:4566 \
    --region=us-east-1 \
    secretsmanager create-secret \
    --name "SYSTEM_USER_SECRET_NAME" \
    --description "System API key for referendum app authentication" \
    --secret-string "$SECRET_VALUE"

if [ $? -eq 0 ]; then
    echo "Successfully created SYSTEM_USER_SECRET_NAME in SecretsManager"
else
    echo "Failed to create secret in SecretsManager"
    exit 1
fi

echo "LocalStack initialization complete!"