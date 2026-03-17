#!/bin/bash
# Script to build and push the Single Docker Image to AWS ECR

# Configure your variables here
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="731083046316"
ECR_REPO_NAME="finops-platform"
IMAGE_TAG="latest"
AWS_PROFILE="dev-plataforma"

# 1. Login to ECR
echo "🔑 Logging into AWS ECR..."
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 2. Build the Docker image
echo "🔨 Building the Single Docker Image ($ECR_REPO_NAME:$IMAGE_TAG)..."
docker build -f Dockerfile.prod -t $ECR_REPO_NAME:$IMAGE_TAG .

# 3. Tag the image for ECR
echo "🏷️ Tagging image for ECR..."
docker tag $ECR_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:$IMAGE_TAG

# 4. Push to ECR
echo "☁️ Pushing image to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:$IMAGE_TAG

echo "✅ Successfully built and pushed $ECR_REPO_NAME:$IMAGE_TAG to ECR!"
echo "➡️ Next step: Update your ECS Service to use this new image tag."
