# Vertex AI Agent Engine Deployment

This directory contains the configuration files needed to deploy the Fact Check Agent to Google Cloud Vertex AI Agent Engine.

## Prerequisites

1. **Google Cloud Project**: Set up a Google Cloud project with billing enabled
2. **APIs Enabled**: Enable the following APIs:
   - Vertex AI API
   - Agent Engine API
   - Secret Manager API (if using secrets)
3. **Authentication**: Set up authentication using one of:
   - Service account key file
   - Application Default Credentials (ADC)
   - gcloud CLI authentication

## Environment Setup

Set the following environment variables:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"  # or your preferred region
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"  # if using service account
```

## Deployment Steps

1. **Install Dependencies**:
   ```bash
   pip install -r deployment/requirements-vertex.txt
   ```

2. **Deploy the Agent**:
   ```bash
   python deployment/vertex_ai_agent.py
   ```

3. **Verify Deployment**:
   The script will output the agent resource name upon successful deployment.

## Agent Capabilities

The deployed agent supports the following operations:

- **Document Analysis**: Analyze documents for fact-checking
- **Text Fact-Checking**: Verify claims in text strings
- **Chat Interface**: Interactive chat for fact-checking queries
- **Session Management**: Create and manage chat sessions

## API Usage

Once deployed, you can interact with the agent through the Vertex AI Agent Engine API:

```python
from google.cloud import aiplatform
from google.cloud.aiplatform import agent_engines

# Initialize the client
client = agent_engines.AgentEngineClient()

# Get your deployed agent
agent = client.get_agent(name="your-agent-resource-name")

# Use the agent for fact-checking
response = agent.analyze_document(file_path="document.pdf", user_id="user123")
```

## Configuration Files

- `vertex_ai_agent.py`: Main deployment script and agent wrapper
- `requirements-vertex.txt`: Python dependencies for Vertex AI deployment
- `README.md`: This documentation file

## Troubleshooting

Common issues and solutions:

1. **Authentication Errors**: Ensure your service account has the required permissions:
   - Vertex AI User
   - Agent Engine Admin
   - Secret Manager Secret Accessor (if using secrets)

2. **Deployment Timeout**: Agent deployment can take several minutes. Be patient.

3. **Resource Errors**: Ensure your project has sufficient quotas for Vertex AI resources.

4. **Import Errors**: Verify all dependencies are correctly specified in requirements-vertex.txt.