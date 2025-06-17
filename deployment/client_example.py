"""
Example client for interacting with the deployed Vertex AI Fact Check Agent
"""
import asyncio
import os
from google.cloud import aiplatform
from google.cloud.aiplatform import agent_engines


class VertexAIFactCheckClient:
    """Client for interacting with deployed Fact Check Agent"""
    
    def __init__(self, agent_resource_name: str, project_id: str, location: str = "us-central1"):
        """
        Initialize the client
        
        Args:
            agent_resource_name: The resource name of the deployed agent
            project_id: Google Cloud project ID
            location: Google Cloud region
        """
        self.agent_resource_name = agent_resource_name
        self.project_id = project_id
        self.location = location
        
        # Initialize aiplatform
        aiplatform.init(project=project_id, location=location)
        
        # Get the deployed agent
        self.agent = agent_engines.get_agent(agent_resource_name)
    
    async def analyze_document(self, file_path: str, user_id: str = "default"):
        """
        Analyze a document for fact-checking
        
        Args:
            file_path: Path to the document to analyze
            user_id: User identifier
            
        Returns:
            Analysis results
        """
        try:
            result = await self.agent.analyze_document(file_path, user_id)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fact_check_text(self, text: str, user_id: str = "default"):
        """
        Fact-check a text string
        
        Args:
            text: Text to fact-check
            user_id: User identifier
            
        Returns:
            Fact-check results
        """
        try:
            result = await self.agent.fact_check_text(text, user_id)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def chat_query(self, user_id: str, session_id: str, message: str):
        """
        Send a chat query to the agent
        
        Args:
            user_id: User identifier
            session_id: Chat session ID
            message: Message to send
            
        Returns:
            Agent response
        """
        try:
            response = await self.agent.chat_query(user_id, session_id, message)
            return response
        except Exception as e:
            return f"Error: {str(e)}"
    
    def create_session(self, user_id: str):
        """
        Create a new chat session
        
        Args:
            user_id: User identifier
            
        Returns:
            Session ID
        """
        try:
            return self.agent.create_session(user_id)
        except Exception as e:
            return f"Error: {str(e)}"


async def example_usage():
    """Example usage of the Vertex AI Fact Check Client"""
    
    # Configuration - replace with your actual values
    AGENT_RESOURCE_NAME = "projects/YOUR_PROJECT/locations/us-central1/agents/YOUR_AGENT_ID"
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
    
    # Initialize client
    client = VertexAIFactCheckClient(
        agent_resource_name=AGENT_RESOURCE_NAME,
        project_id=PROJECT_ID
    )
    
    print("=== Vertex AI Fact Check Agent Client Example ===")
    
    # Example 1: Fact-check text
    print("\n1. Fact-checking text...")
    text = "The Earth is flat and the moon landing was staged in 1969."
    result = await client.fact_check_text(text, "example_user")
    print(f"Result: {result}")
    
    # Example 2: Create chat session and send message
    print("\n2. Chat interaction...")
    user_id = "example_user"
    session_id = client.create_session(user_id)
    print(f"Created session: {session_id}")
    
    if not session_id.startswith("Error"):
        message = "Can you fact-check the claim that vaccines cause autism?"
        response = await client.chat_query(user_id, session_id, message)
        print(f"Agent response: {response}")
    
    # Example 3: Document analysis (if you have a document)
    # print("\n3. Document analysis...")
    # doc_result = await client.analyze_document("path/to/document.pdf", "example_user")
    # print(f"Document analysis: {doc_result}")


if __name__ == "__main__":
    asyncio.run(example_usage())