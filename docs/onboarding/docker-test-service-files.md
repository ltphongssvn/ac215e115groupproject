# Docker Test Service Implementation Files

## 1. Main FastAPI Application

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/main.py`

```python
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/main.py
# Minimal FastAPI application for testing Docker containerization
# This file demonstrates a basic microservice structure with health checks

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import os
import logging

# Configure logging to help with debugging in containers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI instance with metadata
app = FastAPI(
    title="Test Docker Service",
    description="A minimal service for testing Docker containerization",
    version="1.0.0"
)

# Add CORS middleware for browser testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class HealthStatus(BaseModel):
    """Model for health check response"""
    status: str
    timestamp: str
    service: str
    environment: str
    version: str

class TestItem(BaseModel):
    """Model for test data items"""
    id: int
    name: str
    value: float
    created_at: Optional[str] = None

class TestDataResponse(BaseModel):
    """Model for test data response"""
    data: List[TestItem]
    count: int
    timestamp: str

# Application startup event
@app.on_event("startup")
async def startup_event():
    """Log when the service starts"""
    logger.info(f"Starting Test Docker Service in {os.getenv('ENV', 'development')} mode")
    logger.info(f"Service running on port {os.getenv('PORT', '8000')}")

# Health check endpoint - essential for container orchestration
@app.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Health check endpoint to verify service is running.
    Used by Docker, Kubernetes, and load balancers to determine service availability.
    """
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service="test-docker-service",
        environment=os.getenv("ENV", "development"),
        version="1.0.0"
    )

# Root endpoint with API information
@app.get("/")
async def root():
    """
    Root endpoint providing basic service information.
    Useful for quick verification that the service is accessible.
    """
    return {
        "message": "Docker test service is running successfully!",
        "service": "test-docker-service",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/health",
        "timestamp": datetime.now().isoformat()
    }

# Test data endpoint to simulate actual service functionality
@app.get("/api/test-data", response_model=TestDataResponse)
async def get_test_data():
    """
    Return sample data to verify API functionality.
    This simulates the kind of data operations your real services will perform.
    """
    # Simulate data that might come from a database
    test_items = [
        TestItem(
            id=1,
            name="Test Item Alpha",
            value=100.50,
            created_at=datetime.now().isoformat()
        ),
        TestItem(
            id=2,
            name="Test Item Beta",
            value=200.75,
            created_at=datetime.now().isoformat()
        ),
        TestItem(
            id=3,
            name="Test Item Gamma",
            value=300.25,
            created_at=datetime.now().isoformat()
        )
    ]
    
    return TestDataResponse(
        data=test_items,
        count=len(test_items),
        timestamp=datetime.now().isoformat()
    )

# Error simulation endpoint for testing error handling
@app.get("/api/error-test/{error_code}")
async def simulate_error(error_code: int):
    """
    Simulate various HTTP errors for testing error handling.
    Useful for verifying that containerized services handle errors properly.
    """
    error_messages = {
        400: "Bad Request - Invalid input parameters",
        401: "Unauthorized - Authentication required",
        403: "Forbidden - Insufficient permissions",
        404: "Not Found - Resource does not exist",
        500: "Internal Server Error - Something went wrong"
    }
    
    if error_code in error_messages:
        logger.error(f"Simulating error {error_code}: {error_messages[error_code]}")
        raise HTTPException(status_code=error_code, detail=error_messages[error_code])
    
    return {"message": f"No error simulation for code {error_code}"}

# Environment info endpoint for debugging
@app.get("/api/env-info")
async def get_environment_info():
    """
    Return environment information for debugging purposes.
    Helps verify that environment variables are correctly passed to containers.
    """
    # Only include non-sensitive environment variables
    safe_env_vars = {
        "ENV": os.getenv("ENV", "not_set"),
        "PORT": os.getenv("PORT", "not_set"),
        "SERVICE_NAME": os.getenv("SERVICE_NAME", "test-docker-service"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "PYTHON_VERSION": os.sys.version,
    }
    
    return {
        "environment_variables": safe_env_vars,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # This allows running the file directly for local development
    # In production, the container CMD will use uvicorn directly
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
```

## 2. Requirements File

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/requirements.txt`

```txt
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/requirements.txt
# Python dependencies for the test Docker service
# These are minimal requirements to demonstrate containerization

fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2
python-dotenv==1.0.1
```

## 3. Dockerfile

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/Dockerfile`

```dockerfile
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/Dockerfile
# Dockerfile for test service demonstrating best practices

# Use specific Python version for reproducibility
FROM python:3.12.3-slim-bookworm

# Set working directory inside container
WORKDIR /app

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
# These are minimal for our test service
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN groupadd -r appuser && \
    useradd -r -g appuser appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 4. Docker Ignore File

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/.dockerignore`

```
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/.dockerignore
# Files and directories to exclude from Docker build context

# Python files
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Documentation
*.md
README.md
docs/

# Git
.git/
.gitignore

# Docker files (don't need to copy these into image)
Dockerfile
docker-compose.yml
.dockerignore
```

## 5. Environment Variables File

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/.env.example`

```env
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/.env.example
# Example environment variables for the test service
# Copy to .env and modify as needed

# Environment mode
ENV=development

# Service configuration
PORT=8000
SERVICE_NAME=test-docker-service

# Logging
LOG_LEVEL=INFO

# API configuration
API_PREFIX=/api
API_VERSION=v1
```

## 6. Docker Compose File

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/docker-compose.yml`

```yaml
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/docker-compose.yml
# Docker Compose configuration for running the test service

version: '3.8'

services:
  test-service:
    # Build from current directory
    build:
      context: .
      dockerfile: Dockerfile
    
    # Container name for easy reference
    container_name: test-docker-service
    
    # Port mapping: host:container
    ports:
      - "8000:8000"
    
    # Environment variables
    environment:
      - ENV=development
      - PORT=8000
      - SERVICE_NAME=test-docker-service
      - LOG_LEVEL=INFO
    
    # Mount source code for development (enables hot reload)
    volumes:
      - .:/app
    
    # Restart policy
    restart: unless-stopped
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 5s
```

## 7. Makefile for Common Operations

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/Makefile`

```makefile
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/Makefile
# Makefile for common Docker operations

# Variables
IMAGE_NAME = test-docker-service
CONTAINER_NAME = test-docker-service
PORT = 8000

# Default target
.DEFAULT_GOAL := help

# Help command
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Build the Docker image
build: ## Build the Docker image
	docker build -t $(IMAGE_NAME):latest .

# Run the container
run: ## Run the container
	docker run -d --name $(CONTAINER_NAME) -p $(PORT):$(PORT) $(IMAGE_NAME):latest

# Run with docker-compose
up: ## Start services with docker-compose
	docker-compose up -d

# Stop services
down: ## Stop services with docker-compose
	docker-compose down

# View logs
logs: ## View container logs
	docker-compose logs -f

# Run tests
test: ## Run tests in container
	docker run --rm $(IMAGE_NAME):latest python -m pytest

# Clean up
clean: ## Remove container and image
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true
	docker rmi $(IMAGE_NAME):latest || true

# Shell into container
shell: ## Open shell in running container
	docker exec -it $(CONTAINER_NAME) /bin/bash

# Check health
health: ## Check service health
	curl http://localhost:$(PORT)/health | python -m json.tool

.PHONY: help build run up down logs test clean shell health
```

## 8. Test Script

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/test_docker.sh`

```bash
#!/bin/bash
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/test-docker-service/test_docker.sh
# Script to test Docker containerization

set -e  # Exit on error

echo "Testing Docker containerization..."
echo "================================="

# Build the Docker image
echo "1. Building Docker image..."
docker build -t test-docker-service:latest .

# Run the container
echo "2. Starting container..."
docker run -d --name test-docker-service -p 8000:8000 test-docker-service:latest

# Wait for service to be ready
echo "3. Waiting for service to be ready..."
sleep 5

# Test health endpoint
echo "4. Testing health endpoint..."
curl -f http://localhost:8000/health || (echo "Health check failed!" && exit 1)

# Test root endpoint
echo "5. Testing root endpoint..."
curl -f http://localhost:8000/ || (echo "Root endpoint failed!" && exit 1)

# Test data endpoint
echo "6. Testing data endpoint..."
curl -f http://localhost:8000/api/test-data || (echo "Data endpoint failed!" && exit 1)

# Clean up
echo "7. Cleaning up..."
docker stop test-docker-service
docker rm test-docker-service

echo "================================="
echo "All tests passed successfully!"
```

## Usage Instructions

1. **Save all files** to the test-docker-service directory
2. **Make the test script executable**: `chmod +x test_docker.sh`
3. **Run the test**: `./test_docker.sh`

Or use the Makefile:
- `make build` - Build the image
- `make up` - Start with docker-compose
- `make logs` - View logs
- `make down` - Stop services
- `make clean` - Clean up everything
