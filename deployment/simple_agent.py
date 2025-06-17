"""
Simplified Vertex AI Agent for testing deployment
This version doesn't depend on the full fact check agent for testing purposes
"""

import asyncio
import json
from typing import Any, Dict


class SimpleFactCheckAgent:
    """Simplified agent for testing Vertex AI deployment"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.operations = {}

    def set_up(self):
        """Initialize the agent - called after deployment"""
        print("✓ Simple Fact Check Agent initialized")

    def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous query method required by agent_engines"""
        return asyncio.run(self.async_query(request))

    async def async_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous query method required by agent_engines"""
        action = request.get("action", "unknown")
        
        if action == "health_check":
            return {
                "status": "healthy",
                "agent_type": "SimpleFactCheckAgent",
                "message": "Simple agent is running successfully"
            }
        elif action == "fact_check_text":
            text = request.get("text", "")
            return {
                "text": text,
                "result": "This is a simplified fact-check response for testing",
                "confidence": 0.85,
                "sources": ["test-source-1", "test-source-2"]
            }
        else:
            return {"error": f"Unknown action: {action}"}

    def stream_query(self, request: Dict[str, Any]):
        """Synchronous streaming query method"""
        result = self.query(request)
        yield result

    async def async_stream_query(self, request: Dict[str, Any]):
        """Asynchronous streaming query method"""
        result = await self.async_query(request)
        yield result

    def register_operations(self):
        """Register operations method required by agent_engines"""
        return {
            # Synchronous operations
            "": ["query"],
            # Streaming operations
            "stream": ["stream_query"]
        }


def create_simple_agent():
    """Create and return the simple agent"""
    return SimpleFactCheckAgent()