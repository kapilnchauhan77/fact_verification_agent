#!/usr/bin/env python3
"""
Simple ADK Deployment Script for testing
Deploys a minimal agent to Vertex AI
"""
import os
import sys
import asyncio
import json
from pathlib import Path

from google.cloud import aiplatform
from vertexai import agent_engines

from simple_agent import SimpleFactCheckAgent


def get_simple_deployment_config():
    """Get minimal deployment configuration"""
    return {
        "requirements": [
            "google-cloud-aiplatform>=1.40.0",
            "requests>=2.28.0",
        ],
        "env_vars": {
            "GOOGLE_CLOUD_REGION": os.getenv("GOOGLE_CLOUD_REGION", "us-central1"),
        },
        "display_name": "Simple Fact Check Agent",
        "description": "A simple test agent for Vertex AI deployment",
    }


def deploy_simple_agent():
    """Deploy the simple agent to Vertex AI"""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    staging_bucket = os.getenv("STAGING_BUCKET", f"gs://{project_id}-vertex-ai-staging")

    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable must be set")

    aiplatform.init(project=project_id, location=location, staging_bucket=staging_bucket)

    # Create agent instance
    local_agent = SimpleFactCheckAgent()
    config = get_simple_deployment_config()

    print("🚀 Deploying Simple Agent to Vertex AI...")
    print(f"📦 Project: {project_id}")
    print(f"🌍 Location: {location}")

    try:
        remote_agent = agent_engines.create(
            local_agent,
            requirements=config["requirements"],
            env_vars=config["env_vars"],
            display_name=config["display_name"],
            description=config["description"],
        )

        print("✅ Simple agent deployed successfully!")
        return remote_agent

    except Exception as e:
        print(f"❌ Simple agent deployment failed: {e}")
        raise


async def test_simple_agent(agent):
    """Test the deployed simple agent"""
    print("\n🧪 Testing simple agent...")
    
    test_cases = [
        {"action": "health_check"},
        {"action": "fact_check_text", "text": "Test claim for fact checking"}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"  {i}. Testing {test_case.get('action')}...")
        try:
            result = await agent.async_query(test_case)
            print(f"     ✅ Success: {json.dumps(result, indent=2)[:100]}...")
        except Exception as e:
            print(f"     ❌ Error: {e}")


async def main():
    """Main deployment function"""
    print("🚀 Simple Vertex AI Agent Deployment")
    print("=" * 40)
    
    try:
        agent = deploy_simple_agent()
        await test_simple_agent(agent)
        print("\n✅ Simple deployment completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())