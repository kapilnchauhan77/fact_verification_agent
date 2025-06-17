# Dockerfile for Vertex AI Agent Engine deployment
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY deployment/requirements-vertex.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/src/
COPY deployment/vertex_ai_agent.py /app/vertex_ai_agent.py

# Set Python path
ENV PYTHONPATH="/app/src"

# Set default command
CMD ["python", "vertex_ai_agent.py"]