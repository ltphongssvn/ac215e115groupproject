# Python Requirements Files for AC215/E115 Project

## 1. Base Requirements File

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/requirements/base.txt`

```txt
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/requirements/base.txt
# Base requirements for AC215/E115 Group Project
# These packages are fundamental to the project's core functionality

# Web Framework and API Development
fastapi==0.115.0           # Modern, fast web framework for building APIs
uvicorn[standard]==0.32.0  # ASGI server for running FastAPI applications
pydantic==2.9.2            # Data validation using Python type annotations
httpx==0.27.2              # Async HTTP client for making API calls

# Database and ORM
sqlalchemy==2.0.35         # SQL toolkit and Object-Relational Mapping
alembic==1.13.3            # Database migration tool for SQLAlchemy

# Data Analysis and Processing
pandas==2.2.3              # Data manipulation and analysis library
numpy==2.0.2               # Fundamental package for numerical computing
matplotlib==3.9.2          # Plotting and visualization library

# Machine Learning and AI
scikit-learn==1.5.2        # Machine learning library for classical ML algorithms
onnxruntime==1.20.0        # Cross-platform inference for ONNX models
langchain==0.3.3           # Framework for developing LLM applications
langchain-community==0.3.2 # Community integrations for LangChain
langgraph==0.2.34          # Library for building stateful LLM workflows

# Model Conversion
scikit-learn-onnx==1.16.0  # Convert scikit-learn models to ONNX format

# NFL Data (if working with sports analytics)
nfl-data-py==0.3.1         # Library for accessing NFL data

# Utilities
python-dotenv==1.0.1       # Load environment variables from .env file
backoff==2.2.1             # Function decoration for retrying with exponential backoff
```

## 2. Development Requirements File

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/requirements/dev.txt`

```txt
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/requirements/dev.txt
# Development dependencies for AC215/E115 Group Project
# These packages are used during development but not in production

# Include base requirements
-r base.txt

# Testing Framework
pytest==8.3.3              # Testing framework for Python
pytest-asyncio==0.24.0     # Pytest support for asyncio
pytest-cov==5.0.0          # Coverage plugin for pytest
pytest-mock==3.14.0        # Mock/stub helpers for pytest

# Code Quality and Linting
black==24.8.0              # Code formatter
flake8==7.1.1              # Style guide enforcement
mypy==1.11.2               # Static type checker
isort==5.13.2              # Import statement organizer
pylint==3.3.1              # Source code analyzer

# Development Tools
ipython==8.27.0            # Enhanced interactive Python shell
jupyter==1.0.0             # Jupyter notebook environment
notebook==7.2.2            # Jupyter notebook interface
ipdb==0.13.13              # IPython debugger

# Documentation
sphinx==8.0.2              # Documentation generator
sphinx-rtd-theme==2.0.0    # Read the Docs theme for Sphinx

# Pre-commit hooks
pre-commit==3.8.0          # Git hook scripts manager
```

## 3. Production Requirements File

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/requirements/prod.txt`

```txt
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/requirements/prod.txt
# Production dependencies for AC215/E115 Group Project
# Minimal set of packages needed for production deployment

# Include base requirements
-r base.txt

# Production server
gunicorn==23.0.0           # Production WSGI HTTP Server

# Monitoring and Logging
prometheus-client==0.20.0  # Prometheus monitoring integration
structlog==24.4.0          # Structured logging

# Security
cryptography==43.0.1       # Cryptographic recipes and primitives
```

## 4. Main Requirements File (Project Root)

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/requirements.txt`

```txt
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/requirements.txt
# Main requirements file that points to the appropriate environment
# This file exists for compatibility with tools expecting requirements.txt in root

# For development, use:
# -r requirements/dev.txt

# For production, use:
# -r requirements/prod.txt

# Default to development requirements
-r requirements/dev.txt
```

## 5. Python Project Configuration (pyproject.toml)

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/pyproject.toml`

```toml
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/pyproject.toml
# Modern Python project configuration file

[project]
name = "ac215e115-group-project"
version = "0.1.0"
description = "AC215/E115 Group Project - Microservices Architecture with ML Components"
readme = "README.md"
requires-python = ">=3.12"
authors = [
    {name = "Your Team Name", email = "team@example.com"}
]

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 100
target-version = ['py312']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-v --cov=src --cov-report=term-missing"

[tool.pylint.messages_control]
disable = "C0111,R0903"
max-line-length = 100
```

## 6. Environment Variables Template

**File:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/.env.example`

```env
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/.env.example
# Example environment variables file
# Copy this to .env and fill in your actual values

# Application Settings
APP_NAME=AC215E115GroupProject
APP_ENV=development
DEBUG=True

# API Keys (Replace with your actual keys)
OPENAI_API_KEY=your-openai-api-key-here
LANGCHAIN_API_KEY=your-langchain-api-key-here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Google Cloud Platform
GCP_PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1

# AWS (if needed)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
```

## Installation Instructions

1. **Create the requirements directory:**
   ```bash
   mkdir -p requirements
   ```

2. **Save each requirements file in the appropriate location**

3. **Create a virtual environment using your preferred method:**
   
   **Option A: Using venv (built-in)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   ```
   
   **Option B: Using conda**
   ```bash
   conda create -n ac215project python=3.12
   conda activate ac215project
   ```
   
   **Option C: Using uv (fastest)**
   ```bash
   uv venv
   source .venv/bin/activate  # On Linux/Mac
   ```

4. **Install the requirements:**
   ```bash
   # For development
   pip install -r requirements/dev.txt
   
   # For production
   pip install -r requirements/prod.txt
   ```

5. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

## Verification Commands

After installation, verify everything is working:

```bash
# Check Python version
python --version

# List installed packages
pip list

# Run tests (once you have tests)
pytest

# Start the FastAPI development server (once you have an app)
uvicorn main:app --reload
```
