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
