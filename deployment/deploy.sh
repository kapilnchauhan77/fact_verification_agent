#!/bin/bash

# Deployment script for Vertex AI Agent Engine
set -e

echo "=== Vertex AI Agent Engine Deployment ==="

# Check required environment variables
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "Error: GOOGLE_CLOUD_PROJECT environment variable is not set"
    echo "Please set it to your Google Cloud project ID:"
    echo "export GOOGLE_CLOUD_PROJECT='your-project-id'"
    exit 1
fi

if [ -z "$GOOGLE_CLOUD_REGION" ]; then
    echo "Warning: GOOGLE_CLOUD_REGION not set, defaulting to us-central1"
    export GOOGLE_CLOUD_REGION="us-central1"
fi

echo "Project: $GOOGLE_CLOUD_PROJECT"
echo "Region: $GOOGLE_CLOUD_REGION"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "Error: No active gcloud authentication found"
    echo "Please authenticate with: gcloud auth login"
    exit 1
fi

# Set the project
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable aiplatform.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Check if requirements file exists
if [ ! -f "deployment/requirements-vertex.txt" ]; then
    echo "Error: requirements-vertex.txt not found in deployment directory"
    exit 1
fi

# Install dependencies
echo "Installing deployment dependencies..."
pip install -r deployment/requirements-vertex.txt

# Run the deployment
echo "Deploying agent to Vertex AI..."
cd "$(dirname "$0")/.."
python deployment/vertex_ai_agent.py

echo "=== Deployment Complete ==="