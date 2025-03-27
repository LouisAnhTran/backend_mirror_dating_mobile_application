#!/bin/bash

# Exit immediately on error
set -e

# ─────────────────────────────────────────────────────────────
# Step 0: Export requirements.txt from Poetry
echo "🔧 Exporting requirements.txt from Poetry..."
poetry export -f requirements.txt --output requirements.txt --without-hashes

# ─────────────────────────────────────────────────────────────
# Define variables
IMAGE_NAME="louisanhtran/mirror-backend"
PEM_FILE="./scripts/build_and_deploy/mirror-backend.pem"
EC2_USER="ec2-user"
EC2_HOST="ec2-18-140-69-207.ap-southeast-1.compute.amazonaws.com"

# ─────────────────────────────────────────────────────────────
# Ensure .pem file has correct permissions
echo "🔐 Setting correct permissions on $PEM_FILE..."
chmod 400 $PEM_FILE

# ─────────────────────────────────────────────────────────────
# Step 1: Build Docker image
echo "🐳 Building Docker image..."
docker build --platform linux/amd64 -t $IMAGE_NAME .

# ─────────────────────────────────────────────────────────────
# Step 2: Push image to Docker Hub
echo "📦 Pushing Docker image to Docker Hub..."
docker push $IMAGE_NAME

# ─────────────────────────────────────────────────────────────
# Step 3: SSH into EC2 and deploy
echo "🚀 Connecting to EC2 instance and deploying..."
ssh -i "$PEM_FILE" $EC2_USER@$EC2_HOST << EOF
  set -e
  echo "🛑 Stopping current container..."
  docker-compose down

  echo "⬇️ Pulling latest image..."
  docker-compose up --pull always -d

  echo "✅ Deployment complete."
EOF
