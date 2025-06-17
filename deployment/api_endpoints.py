"""
API endpoints for the Vertex AI deployed Fact Check Agent
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, Dict, Any
import tempfile
import os
import asyncio
from pathlib import Path

from vertex_ai_agent import VertexAIFactCheckAgent


app = FastAPI(
    title="Fact Check Agent API",
    description="API for the Vertex AI deployed Fact Check Agent",
    version="1.0.0"
)

# Global agent instance
agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    global agent
    agent = VertexAIFactCheckAgent()


# Request/Response models
class TextFactCheckRequest(BaseModel):
    text: str
    user_id: Optional[str] = "default"


class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


class SessionRequest(BaseModel):
    user_id: str


class SessionResponse(BaseModel):
    session_id: str


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Fact Check Agent API", "status": "active"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent_initialized": agent is not None}


@app.post("/fact-check/text")
async def fact_check_text(request: TextFactCheckRequest):
    """
    Fact-check a text string
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        result = await agent.fact_check_text(request.text, request.user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fact-check/document")
async def fact_check_document(
    file: UploadFile = File(...),
    user_id: str = "default"
):
    """
    Fact-check an uploaded document
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        result = await agent.analyze_document(tmp_file_path, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@app.post("/chat/session", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """
    Create a new chat session
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        session_id = agent.create_session(request.user_id)
        return SessionResponse(session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """
    Send a chat message to the agent
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        # Create session if not provided
        if not request.session_id:
            session_id = agent.create_session(request.user_id)
        else:
            session_id = request.session_id
        
        response = await agent.chat_query(request.user_id, session_id, request.message)
        return ChatResponse(response=response, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/info")
async def agent_info():
    """
    Get information about the agent
    """
    return {
        "name": "Fact Check Agent",
        "version": "1.0.0",
        "capabilities": [
            "text_fact_checking",
            "document_analysis",
            "chat_interface",
            "session_management"
        ],
        "supported_formats": [
            "text/plain",
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)