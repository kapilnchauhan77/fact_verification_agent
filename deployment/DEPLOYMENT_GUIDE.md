# Vertex AI Agent Engine Deployment Guide

Complete guide for deploying the Fact Check Agent to Google Cloud Vertex AI using the Agent Development Kit (ADK) pattern.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Deployment Process](#deployment-process)
4. [Testing](#testing)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)
7. [API Usage](#api-usage)

## Prerequisites

### Required Software
- Python 3.8+ 
- Google Cloud SDK (`gcloud`)
- Docker (for containerized deployment)
- Git

### Required Permissions
Your Google Cloud account needs:
- `roles/aiplatform.admin` - Deploy to Vertex AI
- `roles/iam.serviceAccountAdmin` - Configure service accounts
- `roles/storage.admin` - Manage deployment artifacts
- `roles/secretmanager.admin` - Configure secrets

### Google Cloud Services
Enable these APIs in your project:
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Environment Setup

### 1. Set Environment Variables

```bash
# Required
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"  # or your preferred region

# Optional but recommended
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r deployment/requirements-vertex.txt

# Verify installation
python deployment/test_deployment.py
```

### 3. Configure Authentication

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set default project
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Set default region
gcloud config set compute/region $GOOGLE_CLOUD_REGION
```

## Deployment Process

### Option A: Automated Deployment (Recommended)

#### 1. Run the Deployment Script

```bash
cd deployment/
python deploy_adk.py
```

This script will:
- ✅ Check environment configuration
- ✅ Initialize the Vertex AI agent
- ✅ Generate IAM setup commands
- ✅ Test agent functionality
- ✅ Save deployment configuration

#### 2. Configure IAM Permissions

```bash
# Make script executable and run
chmod +x setup_iam.sh
./setup_iam.sh
```

### Option B: Manual Deployment

#### 1. Initialize Agent

```python
from vertex_ai_agent import deploy_to_vertex_ai

# Deploy the agent
agent = deploy_to_vertex_ai()
```

#### 2. Configure Service Account

```bash
# Create service account for the agent
gcloud iam service-accounts create vertex-ai-agent \
    --display-name="Vertex AI Fact Check Agent"

# Grant required permissions
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:vertex-ai-agent@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:vertex-ai-agent@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:vertex-ai-agent@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

## Testing

### 1. Run Deployment Tests

```bash
# Test basic functionality
python deployment/test_deployment.py

# Test ADK deployment
python deployment/deploy_adk.py
```

### 2. Test API Endpoints

```python
import asyncio
from vertex_ai_agent import VertexAIFactCheckAgent

async def test_agent():
    agent = VertexAIFactCheckAgent()
    
    # Health check
    health = agent.health_check()
    print(f"Health: {health}")
    
    # Create session
    session_id = agent.create_session("test_user")
    print(f"Session: {session_id}")
    
    # Fact check text
    result = await agent.fact_check_text(
        "The Earth is round and orbits the Sun.", 
        "test_user"
    )
    print(f"Result: {result}")

asyncio.run(test_agent())
```

### 3. Load Testing

```bash
# Install load testing tools
pip install locust

# Run load tests (create test_load.py first)
locust -f test_load.py --host=http://localhost:8000
```

## Monitoring

### 1. Vertex AI Console

Monitor your deployed agent at:
```
https://console.cloud.google.com/vertex-ai/agents
```

### 2. Cloud Logging

View logs using:
```bash
gcloud logging read "resource.type=vertex_ai_agent" --limit=50
```

### 3. Metrics and Alerts

Set up monitoring in Cloud Monitoring:
- Agent response time
- Error rates
- Resource utilization
- Request volume

## API Usage

### Request Format

The agent accepts requests with the following structure:

```json
{
  "action": "fact_check_text|analyze_document|chat_query|create_session|health_check",
  "user_id": "string",
  "text": "string (for fact_check_text)",
  "file_path": "string (for analyze_document)",
  "session_id": "string (for chat_query)",
  "message": "string (for chat_query)"
}
```

### Example Requests

#### Fact Check Text
```python
request = {
    "action": "fact_check_text",
    "user_id": "user123",
    "text": "The Earth is flat and the moon landing was fake."
}

result = await agent.process_request(request)
```

#### Analyze Document
```python
request = {
    "action": "analyze_document", 
    "user_id": "user123",
    "file_path": "/path/to/document.pdf"
}

result = await agent.process_request(request)
```

#### Chat Query
```python
# First create a session
session_request = {
    "action": "create_session",
    "user_id": "user123"
}
session_result = await agent.process_request(session_request)
session_id = session_result["session_id"]

# Then send chat message
chat_request = {
    "action": "chat_query",
    "user_id": "user123", 
    "session_id": session_id,
    "message": "What is fact-checking?"
}

result = await agent.process_request(chat_request)
```

### Response Format

All responses follow this structure:

```json
{
  "success": true|false,
  "results": [...],  // For successful fact-checking
  "session_id": "string",  // For session creation
  "status": "string",  // For health checks
  "error": "string"  // For errors
}
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Error: cannot import name 'agent_engines'
# Solution: The agent_engines module is not yet available in all regions
# The deployment uses ADK patterns and will work when the module becomes available
```

#### 2. Authentication Errors
```bash
# Error: Could not automatically determine credentials
# Solution: Set GOOGLE_APPLICATION_CREDENTIALS or run gcloud auth login
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

#### 3. Permission Errors
```bash
# Error: Permission denied
# Solution: Run the IAM setup script
./setup_iam.sh
```

#### 4. Dependency Issues
```bash
# Error: Module not found
# Solution: Install all requirements
pip install -r deployment/requirements-vertex.txt
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Deploy with debug info
agent = deploy_to_vertex_ai()
```

### Health Checks

Monitor agent health:

```python
health = agent.health_check()
if health["status"] != "healthy":
    print(f"Agent unhealthy: {health}")
```

## Security Best Practices

### 1. Service Account Security
- Use least privilege principle
- Rotate service account keys regularly
- Enable audit logging

### 2. Network Security
- Use VPC firewall rules
- Enable Private Google Access
- Implement SSL/TLS encryption

### 3. Secret Management
- Store API keys in Secret Manager
- Never commit secrets to code
- Use workload identity when possible

## Performance Optimization

### 1. Scaling Configuration
```python
# Configure for high traffic
config = {
    "min_replicas": 1,
    "max_replicas": 10,
    "cpu_limit": "2",
    "memory_limit": "4Gi"
}
```

### 2. Caching Strategy
- Enable response caching
- Use Cloud CDN for static content
- Implement database connection pooling

### 3. Monitoring and Alerting
- Set up latency alerts
- Monitor error rates
- Track resource utilization

## Cost Management

### 1. Resource Optimization
- Use appropriate machine types
- Enable autoscaling
- Monitor usage patterns

### 2. Budget Alerts
```bash
# Set up budget alerts
gcloud billing budgets create \
    --billing-account=$BILLING_ACCOUNT \
    --display-name="Vertex AI Agent Budget" \
    --budget-amount=100
```

## Support and Resources

### Documentation
- [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine)
- [Google Cloud ADK](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/deploy)

### Community
- [Google Cloud Community](https://cloud.google.com/community)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/vertex-ai)

### Contact
For issues with this deployment:
1. Check the troubleshooting section
2. Review logs in Cloud Console
3. Create an issue in the project repository

---

## Quick Start Checklist

- [ ] Set environment variables
- [ ] Install dependencies
- [ ] Run deployment script
- [ ] Configure IAM permissions
- [ ] Test basic functionality
- [ ] Set up monitoring
- [ ] Configure alerts
- [ ] Review security settings

**Deployment time:** ~15-20 minutes  
**Prerequisites time:** ~10-15 minutes  
**Total setup time:** ~30-35 minutes