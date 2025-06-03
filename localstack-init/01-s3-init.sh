#!/bin/bash
set -e

echo "S3 initialization starting..."

# Use localhost since we're running inside the LocalStack container
ENDPOINT="http://localhost:4566"

echo "Waiting for services to be ready..."
for i in {1..30}; do
    if curl -s "$ENDPOINT/_localstack/health" | grep -q '"s3": "available"'; then
        echo "S3 service is available!"
        break
    fi
    echo "Attempt $i: Waiting for S3 service..."
    sleep 2
done

echo "Creating S3 bucket..."
aws --endpoint-url="$ENDPOINT" \
    --region=us-east-1 \
    s3 mb s3://bill-texts

# Set bucket policy
aws --endpoint-url="$ENDPOINT" \
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
