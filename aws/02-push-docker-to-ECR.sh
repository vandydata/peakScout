#!/bin/bash
set -e

# Configuration
REGION="us-east-1"
REPO_NAME="peakscout-lambda"
IMAGE_TAG="latest"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}"

echo "Pushing to ECR: ${ECR_URI}:${IMAGE_TAG}"

# Login to ECR
aws ecr get-login-password --region ${REGION} | \
    docker login --username AWS --password-stdin ${ECR_URI}

echo "Tagging image"
docker tag peakscout-lambda:latest ${ECR_URI}:${IMAGE_TAG}

echo "Pushing to ECR"
docker push ${ECR_URI}:${IMAGE_TAG}

echo "Pushed to ECR. Use this URI when creating your Lambda functio:"
echo "Image URI: ${ECR_URI}:${IMAGE_TAG}"
