#!/usr/bin/env python3
"""
Check deployment status and get better error information
"""
import os
from google.cloud import aiplatform
from vertexai import reasoning_engines

def check_deployment_status():
    """Check the status of recent deployments"""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    
    aiplatform.init(project=project_id, location=location)
    
    try:
        # List reasoning engines
        print("🔍 Checking reasoning engines...")
        engines = reasoning_engines.ReasoningEngine.list()
        
        for engine in engines:
            print(f"Engine: {engine.resource_name}")
            print(f"Display Name: {engine.display_name}")
            print(f"State: {engine.state}")
            print(f"Create Time: {engine.create_time}")
            print("---")
            
            # Try to get more details
            try:
                details = engine.get()
                print(f"Details: {details}")
            except Exception as e:
                print(f"Error getting details: {e}")
            print("="*50)
            
    except Exception as e:
        print(f"Error listing engines: {e}")

if __name__ == "__main__":
    check_deployment_status()