# /home/lenovo/code/ltphongssvn/ac215e115groupproject/docs/onboarding/docker-containerization-guide.md
# Docker Containerization Guide for AC215/E115 Microservices
# Complete guide for containerizing Python microservices with best practices

## Understanding Docker in Our Architecture

Before diving into commands and configurations, let's understand why Docker is essential for our microservices architecture. Our ERP AI system consists of three main services - the NL+SQL agent, RAG orchestrator, and time-series forecasting engine - each potentially requiring different Python versions, system libraries, or conflicting dependencies. Docker solves this by wrapping each service in its own isolated container, complete with its specific environment, ensuring that what works on your laptop will work identically in production on Google Kubernetes Engine.

Think of Docker containers as self-contained apartments in a large building. Each apartment (container) has its own furniture, utilities, and layout (dependencies and configuration), but they all share the building's infrastructure (the host operating system's kernel). This is more efficient than having separate houses (virtual machines) for each service, while still maintaining isolation and independence.

## Prerequisites and Installation

### System Requirements

Before we begin containerizing our services, ensure your development machine meets these requirements:
- Ubuntu 24.04 LTS or compatible Linux distribution (as per your current setup)
- At least 10GB free disk space for Docker images
- 8GB RAM minimum (16GB recommended for running multiple containers)
- CPU with virtualization support enabled in BIOS

### Installing Docker Engine

Docker installation on Ubuntu involves adding Docker's official repository and installing the Docker Engine. We're not using Docker Desktop because we're on Linux, where Docker Engine runs natively without the overhead of a virtual machine:

```bash
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/scripts/install-docker.sh
# Script to install Docker Engine on Ubuntu

#!/bin/bash
set -e  # Exit on any error

echo "Installing Docker Engine for Ubuntu..."

# Remove any old Docker installations that might conflict
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Update package index and install prerequisites
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key for package verification
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine, CLI, and containerd
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add current user to docker group to run without sudo
sudo usermod -aG docker $USER

echo "Docker installation complete!"
echo "Please log out and back in for group changes to take effect."
docker --version
```

### Post-Installation Setup

After installing Docker, you need to configure it for optimal development experience:

```bash
# Verify Docker installation
docker --version
docker compose version

# Test Docker with hello-world image
docker run hello-world

# Configure Docker to start on boot
sudo systemctl enable docker.service
sudo systemctl enable containerd.service
```

## Project Dockerfile Structure

Our microservices architecture requires a thoughtful approach to Dockerfile organization. Each service gets its own Dockerfile, but they share common patterns. Let's create a base Dockerfile that other services can build upon:

### Base Python Image Configuration

```dockerfile
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/docker/python-base/Dockerfile
# Base Python image with common dependencies for all microservices
# This creates a reusable foundation that all services build upon

# Use official Python runtime as base image
# We specify exact version for reproducibility across environments
FROM python:3.12.3-slim-bookworm

# Set environment variables for Python optimization
# PYTHONDONTWRITEBYTECODE prevents Python from writing .pyc files
# PYTHONUNBUFFERED ensures stdout/stderr are unbuffered for better logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # pip configuration for better container builds
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies that many Python packages require
# These are common C libraries needed by packages like numpy, pandas
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials for packages that compile C extensions
    build-essential \
    # PostgreSQL client libraries for psycopg2
    libpq-dev \
    # Git for installing packages from repositories
    git \
    # Curl and wget for downloading files in scripts
    curl \
    wget \
    # Clean up apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
# Running containers as root is a security risk
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy and install base Python requirements
# We copy requirements first to leverage Docker's layer caching
COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --upgrade pip && \
    pip install -r /app/requirements/base.txt

# Switch to non-root user
USER appuser

# Health check command (services will override this)
HEALTHCHECK CMD python -c "import sys; sys.exit(0)"
```

### Service-Specific Dockerfiles

Now let's create Dockerfiles for each of our three main services, each building upon our base image but adding service-specific configurations:

```dockerfile
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/services/nl-sql-agent/Dockerfile
# NL+SQL Agent Service container
# Handles natural language to SQL query translation

# Build from our common base image
FROM python-base:latest

# Switch back to root to install service-specific dependencies
USER root

# Install additional system packages specific to NL+SQL service
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Additional PostgreSQL tools for SQL manipulation
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy service-specific requirements
COPY services/nl-sql-agent/requirements.txt /app/service-requirements.txt
RUN pip install -r /app/service-requirements.txt

# Copy application code
# We copy the entire service directory
COPY --chown=appuser:appuser services/nl-sql-agent /app/services/nl-sql-agent

# Copy shared utilities if any
COPY --chown=appuser:appuser shared /app/shared

# Switch back to non-root user
USER appuser

# Set the service directory as working directory
WORKDIR /app/services/nl-sql-agent

# Expose the port this service runs on
EXPOSE 8001

# Define the command to run the service
# Using uvicorn with specific workers for production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]

# Health check specific to this service
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1
```

```dockerfile
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/services/rag-orchestrator/Dockerfile
# RAG Orchestrator Service container
# Manages document retrieval and generation

FROM python-base:latest

USER root

# RAG service needs additional ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    # HDF5 libraries for storing large numerical datasets
    libhdf5-dev \
    # Graphics libraries sometimes needed by ML visualization
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

COPY services/rag-orchestrator/requirements.txt /app/service-requirements.txt
RUN pip install -r /app/service-requirements.txt

COPY --chown=appuser:appuser services/rag-orchestrator /app/services/rag-orchestrator
COPY --chown=appuser:appuser shared /app/shared

USER appuser
WORKDIR /app/services/rag-orchestrator

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1
```

```dockerfile
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/services/ts-forecasting/Dockerfile
# Time-Series Forecasting Service container
# Provides price predictions using ML models

FROM python-base:latest

USER root

# Time-series analysis often needs statistical libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Fortran libraries for scientific computing
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

COPY services/ts-forecasting/requirements.txt /app/service-requirements.txt
RUN pip install -r /app/service-requirements.txt

COPY --chown=appuser:appuser services/ts-forecasting /app/services/ts-forecasting
COPY --chown=appuser:appuser shared /app/shared

USER appuser
WORKDIR /app/services/ts-forecasting

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "2"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1
```

## Multi-Stage Builds for Production

Multi-stage builds are crucial for creating lean production images. The concept is like cooking a meal where you do all the prep work in the kitchen (build stage) but only bring the finished dish to the table (production stage), leaving all the cooking utensils and scraps behind:

```dockerfile
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/docker/production/Dockerfile.multistage
# Multi-stage build example for production deployments
# This significantly reduces final image size

# Stage 1: Builder stage with all compilation tools
FROM python:3.12.3-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git

# Create virtual environment in builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install all requirements
COPY requirements/base.txt requirements/prod.txt /tmp/
RUN pip install --upgrade pip && \
    pip install -r /tmp/base.txt && \
    pip install -r /tmp/prod.txt

# Stage 2: Runtime stage with minimal dependencies
FROM python:3.12.3-slim-bookworm

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code
WORKDIR /app
COPY --chown=appuser:appuser . /app

USER appuser

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose for Local Development

Docker Compose orchestrates multiple containers for local development, simulating your production environment on your laptop. This is essential for testing how your microservices interact before deploying to Kubernetes:

```yaml
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/docker-compose.yml
# Docker Compose configuration for local development
# This file orchestrates all services and their dependencies

version: '3.8'

# Define named networks for service communication
networks:
  app-network:
    driver: bridge
  db-network:
    driver: bridge

# Define named volumes for persistent data
volumes:
  postgres-data:
  redis-data:
  chroma-data:

services:
  # PostgreSQL database for ERP data
  postgres:
    image: postgres:15-alpine
    container_name: erp-postgres
    environment:
      POSTGRES_DB: erp_db
      POSTGRES_USER: ${DB_USER:-erpuser}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-secret}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./infrastructure/db/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - db-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U erpuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis for caching and session management
  redis:
    image: redis:7-alpine
    container_name: erp-redis
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Chroma vector database for RAG
  chroma:
    image: chromadb/chroma:latest
    container_name: erp-chroma
    environment:
      - PERSIST_DIRECTORY=/data
      - ANONYMIZED_TELEMETRY=false
    volumes:
      - chroma-data:/data
    ports:
      - "8000:8000"
    networks:
      - app-network

  # API Gateway
  api-gateway:
    build:
      context: .
      dockerfile: api-gateway/Dockerfile
    container_name: erp-api-gateway
    environment:
      - ENV=development
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET:-your-secret-key}
    ports:
      - "80:80"
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - app-network
    volumes:
      # Mount source code for hot reloading in development
      - ./api-gateway:/app/api-gateway
      - ./shared:/app/shared

  # NL+SQL Agent Service
  nl-sql-agent:
    build:
      context: .
      dockerfile: services/nl-sql-agent/Dockerfile
    container_name: nl-sql-agent
    environment:
      - DATABASE_URL=postgresql://${DB_USER:-erpuser}:${DB_PASSWORD:-secret}@postgres:5432/erp_db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=DEBUG
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
      - db-network
    volumes:
      - ./services/nl-sql-agent:/app/services/nl-sql-agent
      - ./shared:/app/shared
    ports:
      - "8001:8001"

  # RAG Orchestrator Service
  rag-orchestrator:
    build:
      context: .
      dockerfile: services/rag-orchestrator/Dockerfile
    container_name: rag-orchestrator
    environment:
      - CHROMA_URL=http://chroma:8000
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=DEBUG
    depends_on:
      - chroma
      - redis
    networks:
      - app-network
    volumes:
      - ./services/rag-orchestrator:/app/services/rag-orchestrator
      - ./shared:/app/shared
    ports:
      - "8002:8002"

  # Time-Series Forecasting Service
  ts-forecasting:
    build:
      context: .
      dockerfile: services/ts-forecasting/Dockerfile
    container_name: ts-forecasting
    environment:
      - DATABASE_URL=postgresql://${DB_USER:-erpuser}:${DB_PASSWORD:-secret}@postgres:5432/erp_db
      - REDIS_URL=redis://redis:6379
      - MODEL_PATH=/app/models
      - LOG_LEVEL=DEBUG
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
      - db-network
    volumes:
      - ./services/ts-forecasting:/app/services/ts-forecasting
      - ./shared:/app/shared
      - ./models:/app/models
    ports:
      - "8003:8003"
```

## Docker Commands and Best Practices

Understanding Docker commands thoroughly will make you more effective at debugging and developing:

### Essential Docker Commands

```bash
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/scripts/docker-commands.sh
# Common Docker commands for development

# Building images
docker build -t erp/nl-sql-agent:latest -f services/nl-sql-agent/Dockerfile .
docker build -t erp/rag-orchestrator:latest -f services/rag-orchestrator/Dockerfile .
docker build -t erp/ts-forecasting:latest -f services/ts-forecasting/Dockerfile .

# Running containers individually
docker run -d --name nl-sql-agent -p 8001:8001 erp/nl-sql-agent:latest
docker run -it --rm erp/nl-sql-agent:latest /bin/bash  # Interactive debugging

# Container management
docker ps                          # List running containers
docker ps -a                       # List all containers
docker logs nl-sql-agent          # View container logs
docker logs -f nl-sql-agent       # Follow logs in real-time
docker exec -it nl-sql-agent /bin/bash  # Enter running container

# Cleanup commands
docker stop $(docker ps -aq)      # Stop all containers
docker rm $(docker ps -aq)        # Remove all containers
docker rmi $(docker images -q)    # Remove all images
docker system prune -a            # Clean everything (careful!)

# Docker Compose commands
docker compose up                 # Start all services
docker compose up -d              # Start in background
docker compose up --build         # Rebuild images then start
docker compose down               # Stop and remove containers
docker compose down -v            # Also remove volumes
docker compose logs -f            # Follow all service logs
docker compose logs -f nl-sql-agent  # Follow specific service
docker compose ps                 # List compose services
docker compose exec nl-sql-agent /bin/bash  # Enter service container
```

### Docker Build Optimization

Optimizing your Docker builds saves time and reduces image size:

```dockerfile
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/docker/optimized/Dockerfile.example
# Example of optimized Dockerfile with best practices

FROM python:3.12.3-slim-bookworm

# Combine RUN commands to reduce layers
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

# Copy requirements first for better caching
COPY requirements/base.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy source code last (changes most frequently)
COPY . /app
WORKDIR /app

# Use specific ENTRYPOINT for consistency
ENTRYPOINT ["python"]
CMD ["main.py"]
```

## Environment Variables and Secrets Management

Managing configuration and secrets properly is crucial for security:

```bash
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/.env.docker
# Docker-specific environment variables
# Never commit this file - it contains secrets!

# Database configuration
DB_USER=erpuser
DB_PASSWORD=your-secure-password-here
DATABASE_URL=postgresql://erpuser:your-secure-password-here@postgres:5432/erp_db

# API Keys
OPENAI_API_KEY=sk-your-openai-key-here
LANGCHAIN_API_KEY=your-langchain-key-here

# Service configuration
REDIS_URL=redis://redis:6379
CHROMA_URL=http://chroma:8000

# JWT configuration
JWT_SECRET=your-very-long-random-string-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=json

# Feature flags
ENABLE_METRICS=true
ENABLE_TRACING=true
```

## Docker Networking Explained

Docker networking allows containers to communicate. In our compose file, we defined two networks:
- `app-network`: For service-to-service communication
- `db-network`: For database access (more restricted)

Services on the same network can reach each other using service names as hostnames. For example, the NL+SQL agent connects to PostgreSQL using `postgres:5432`, not `localhost:5432`.

## Volume Management

Volumes persist data beyond container lifecycle:

```bash
# List all volumes
docker volume ls

# Inspect a volume
docker volume inspect ac215e115groupproject_postgres-data

# Create a backup of PostgreSQL data
docker run --rm \
    -v ac215e115groupproject_postgres-data:/data \
    -v $(pwd)/backups:/backup \
    alpine tar czf /backup/postgres-backup.tar.gz /data

# Restore from backup
docker run --rm \
    -v ac215e115groupproject_postgres-data:/data \
    -v $(pwd)/backups:/backup \
    alpine tar xzf /backup/postgres-backup.tar.gz -C /
```

## Debugging Containerized Services

When services don't work as expected, these debugging techniques help:

```bash
# Check if container is running
docker ps | grep nl-sql-agent

# Inspect container configuration
docker inspect nl-sql-agent

# View real-time resource usage
docker stats

# Check network connectivity
docker compose exec nl-sql-agent ping postgres
docker compose exec nl-sql-agent curl http://rag-orchestrator:8002/health

# Debug Python application
docker compose exec nl-sql-agent python -m pdb main.py

# Copy files from container for inspection
docker cp nl-sql-agent:/app/logs/error.log ./local-error.log
```

## CI/CD Integration

Integrating Docker with GitHub Actions for automated builds:

```yaml
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/.github/workflows/docker-build.yml
# GitHub Actions workflow for building and testing Docker images

name: Docker Build and Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to GitHub Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push NL-SQL Agent
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./services/nl-sql-agent/Dockerfile
        push: true
        tags: ghcr.io/${{ github.repository }}/nl-sql-agent:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max
    
    - name: Run tests in container
      run: |
        docker run --rm \
          ghcr.io/${{ github.repository }}/nl-sql-agent:latest \
          pytest /app/tests
```

## Performance Monitoring

Monitor your containerized services for optimal performance:

```yaml
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/docker-compose.monitoring.yml
# Additional services for monitoring

version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    networks:
      - app-network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_USER=${GF_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GF_PASSWORD:-admin}
    ports:
      - "3000:3000"
    networks:
      - app-network

volumes:
  prometheus-data:
  grafana-data:
```

## Security Best Practices

Security should be built into your Docker workflow from the start:

1. **Never run containers as root** - Always create and use a non-root user
2. **Scan images for vulnerabilities** - Use tools like Trivy or Snyk
3. **Use specific version tags** - Never use `latest` in production
4. **Minimize image size** - Smaller images have smaller attack surfaces
5. **Don't store secrets in images** - Use environment variables or secret management tools
6. **Keep base images updated** - Regularly rebuild with updated base images

```bash
# Scan an image for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image erp/nl-sql-agent:latest
```

## Troubleshooting Common Issues

### Container Exits Immediately
Check logs to see why: `docker logs container-name`
Common causes: Missing environment variables, syntax errors in CMD

### Cannot Connect to Service
Verify network: Services must be on same network
Check port mapping: Ensure ports are exposed and mapped correctly
Test DNS resolution: `docker exec container-1 nslookup container-2`

### Out of Disk Space
Clean up: `docker system prune -a --volumes`
Check disk usage: `docker system df`
Move Docker root: Configure Docker to use different disk

### Slow Build Times
Use .dockerignore to exclude unnecessary files
Leverage build cache by ordering Dockerfile commands correctly
Use BuildKit: `DOCKER_BUILDKIT=1 docker build .`

## Next Steps

With Docker containerization in place, your next steps are:
1. Create actual service code in the service directories
2. Write comprehensive tests that run in containers
3. Set up Kubernetes manifests for production deployment
4. Implement service mesh for advanced networking
5. Add observability with distributed tracing

This containerization foundation supports your microservices architecture, enabling independent development, testing, and deployment of each service while maintaining consistency through shared base images and configuration patterns.