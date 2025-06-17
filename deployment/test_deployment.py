"""
Test script for validating the Vertex AI deployment configuration
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from deploy_adk import VertexAIFactCheckAgent


async def test_agent_initialization():
    """Test that the agent can be initialized"""
    print("Testing agent initialization...")
    try:
        agent = VertexAIFactCheckAgent()
        print("✓ Agent initialized successfully")
        return agent
    except Exception as e:
        print(f"✗ Agent initialization failed: {e}")
        return None


async def test_text_fact_checking(agent):
    """Test text fact-checking functionality"""
    print("\nTesting text fact-checking...")
    try:
        test_text = "The Earth is round and orbits the Sun."
        result = await agent.fact_check_text(test_text, "test_user")
        
        if result.get('success'):
            print("✓ Text fact-checking successful")
            print(f"  Found {len(result.get('results', []))} claims")
        else:
            print(f"✗ Text fact-checking failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"✗ Text fact-checking error: {e}")


async def test_session_creation(agent):
    """Test session creation"""
    print("\nTesting session creation...")
    try:
        session_id = agent.create_session("test_user")
        print(f"✓ Session created successfully: {session_id}")
        return session_id
    except Exception as e:
        print(f"✗ Session creation failed: {e}")
        return None


async def test_chat_functionality(agent, session_id):
    """Test chat functionality"""
    print("\nTesting chat functionality...")
    try:
        if not session_id:
            print("✗ No session ID available for chat test")
            return
            
        message = "What is fact-checking?"
        response = await agent.chat_query("test_user", session_id, message)
        print(f"✓ Chat response received: {response[:100]}...")
        
    except Exception as e:
        print(f"✗ Chat functionality error: {e}")


def test_environment_variables():
    """Test that required environment variables are set"""
    print("Testing environment variables...")
    
    required_vars = ["GOOGLE_CLOUD_PROJECT"]
    optional_vars = ["GOOGLE_CLOUD_REGION", "GOOGLE_APPLICATION_CREDENTIALS"]
    
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        print(f"✗ Missing required environment variables: {', '.join(missing_required)}")
        return False
    else:
        print("✓ Required environment variables are set")
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✓ Optional variable {var} is set")
        else:
            print(f"! Optional variable {var} is not set")
    
    return True


def test_import_dependencies():
    """Test that all required dependencies can be imported"""
    print("\nTesting dependency imports...")
    
    dependencies = [
        ("google.cloud.aiplatform", "Google Cloud AI Platform"),
        ("google.generativeai", "Google Generative AI"),
        ("aiohttp", "aiohttp"),
        ("bs4", "BeautifulSoup4"),
        ("requests", "requests"),
        ("pydantic", "Pydantic"),
        ("sklearn", "scikit-learn"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas")
    ]
    
    failed_imports = []
    
    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {display_name} imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import {display_name}: {e}")
            failed_imports.append(display_name)
    
    return len(failed_imports) == 0


async def run_all_tests():
    """Run all deployment tests"""
    print("=== Vertex AI Deployment Test Suite ===\n")
    
    # Test 1: Environment variables
    env_ok = test_environment_variables()
    
    # Test 2: Import dependencies
    imports_ok = test_import_dependencies()
    
    if not imports_ok:
        print("\n✗ Dependency import test failed. Please install requirements:")
        print("pip install -r deployment/requirements-vertex.txt")
        return
    
    # Test 3: Agent initialization
    agent = await test_agent_initialization()
    
    if not agent:
        print("\n✗ Agent initialization failed. Cannot proceed with functional tests.")
        return
    
    # Test 4: Text fact-checking
    await test_text_fact_checking(agent)
    
    # Test 5: Session creation
    session_id = await test_session_creation(agent)
    
    # Test 6: Chat functionality
    await test_chat_functionality(agent, session_id)
    
    print("\n=== Test Suite Complete ===")
    
    if env_ok and imports_ok and agent:
        print("✓ Deployment configuration appears to be valid")
        print("You can proceed with deployment using: ./deployment/deploy.sh")
    else:
        print("✗ Some tests failed. Please address the issues before deployment.")


if __name__ == "__main__":
    asyncio.run(run_all_tests())