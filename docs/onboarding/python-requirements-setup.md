# /home/lenovo/code/ltphongssvn/ac215e115groupproject/docs/onboarding/python-requirements-setup.md
# Python Requirements Files for AC215/E115 Project
# Last Updated: 2024 with critical dependency fixes

## ⚠️ Critical Compatibility Notice

**IMPORTANT**: This project requires specific package versions to maintain compatibility between all components. Two critical issues have been identified and resolved:

1. **NumPy must be version 1.26.4** (not 2.x) due to LangChain compatibility requirements
2. **The ONNX converter package is named `skl2onnx`** (not `scikit-learn-onnx`) on PyPI

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
numpy==1.26.4              # CRITICAL: Must use 1.26.4 for LangChain compatibility (NOT 2.x)
matplotlib==3.9.2          # Plotting and visualization library

# Machine Learning and AI
scikit-learn==1.5.2        # Machine learning library for classical ML algorithms
onnxruntime==1.20.0        # Cross-platform inference for ONNX models
langchain==0.3.3           # Framework for developing LLM applications (requires numpy<2.0)
langchain-community==0.3.2 # Community integrations for LangChain
langgraph==0.2.34          # Library for building stateful LLM workflows

# Model Conversion
skl2onnx==1.16.0           # Convert scikit-learn models to ONNX format (correct PyPI name)

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

## Known Compatibility Issues and Solutions

### Issue 1: NumPy Version Conflict with LangChain

**Problem**: LangChain 0.3.3 requires `numpy<2.0.0`, but initial requirements specified `numpy==2.0.2`.

**Error Message You'll See**:
```
ERROR: Cannot install langchain==0.3.3 and numpy==2.0.2 because these package versions have conflicting dependencies.
```

**Root Cause**: LangChain hasn't been updated to support NumPy 2.x breaking changes in array handling APIs.

**Solution**: Use `numpy==1.26.4` (the latest stable 1.x version that's compatible with all project dependencies).

### Issue 2: Incorrect Package Name for ONNX Converter

**Problem**: The package name `scikit-learn-onnx` doesn't exist on PyPI.

**Error Message You'll See**:
```
ERROR: Could not find a version that satisfies the requirement scikit-learn-onnx==1.16.0
ERROR: No matching distribution found for scikit-learn-onnx==1.16.0
```

**Root Cause**: The actual PyPI package name is `skl2onnx`, not `scikit-learn-onnx`. This is a common naming confusion in the Python ecosystem.

**Solution**: Use `skl2onnx==1.16.0` in requirements files.

## Installation Instructions

### Prerequisites

1. **Python Version**: This project requires Python 3.12.x
   ```bash
   python --version  # Should show Python 3.12.x
   ```

2. **Conda Environment**: We recommend using the project's conda environment
   ```bash
   conda create -n test_ac215 python=3.12
   conda activate test_ac215
   ```

### Step-by-Step Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd ac215e115groupproject
   ```

2. **Activate the conda environment**:
   ```bash
   conda activate test_ac215
   ```

3. **Install the requirements**:
   ```bash
   # For development work
   pip install -r requirements/dev.txt
   
   # For production deployment
   pip install -r requirements/prod.txt
   ```

4. **Verify critical packages**:
   ```bash
   python -c "import numpy, langchain; print(f'NumPy: {numpy.__version__}'); print(f'LangChain: {langchain.__version__}')"
   ```
   
   Expected output:
   ```
   NumPy: 1.26.4
   LangChain: 0.3.3
   ```

5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys and configuration
   ```

## Troubleshooting Guide

### If Installation Fails

1. **Clear pip cache** (sometimes corrupted cache causes issues):
   ```bash
   pip cache purge
   ```

2. **Ensure you're in the correct environment**:
   ```bash
   conda info --envs  # Should show test_ac215 as active (marked with *)
   ```

3. **Check Python version**:
   ```bash
   python --version  # Must be 3.12.x, not 3.13 or 3.11
   ```

4. **Manually verify the two critical fixes in requirements/base.txt**:
   ```bash
   grep "numpy==" requirements/base.txt     # Should show numpy==1.26.4
   grep "skl2onnx==" requirements/base.txt  # Should show skl2onnx==1.16.0
   ```

### Common Error Messages and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `ResolutionImpossible` | Package version conflicts | Check numpy is 1.26.4, not 2.x |
| `No matching distribution found for scikit-learn-onnx` | Wrong package name | Use `skl2onnx` instead |
| `ModuleNotFoundError: No module named 'fastapi'` | Not in correct environment | Run `conda activate test_ac215` |
| `pip is looking at multiple versions...` | Complex dependency resolution | Be patient, this can take 2-3 minutes |

## Verification Commands

After successful installation, run these checks:

```bash
# Check all base packages are installed
python -c "import fastapi, pydantic, langchain, pandas, numpy, sklearn; print('All base packages OK')"

# Check FastAPI is working
python -c "from fastapi import FastAPI; app = FastAPI(); print('FastAPI OK')"

# Check WebSocket support (comes with uvicorn[standard])
python -c "import websockets; print(f'WebSockets version: {websockets.__version__}')"

# List all installed packages with versions
pip list | grep -E "fastapi|langchain|numpy|pandas|sklearn"
```

## Next Steps After Installation

1. **Test the FastAPI setup**: Create a simple test service to verify everything works
2. **Review the architecture documents**: Understand the three microservices (NL+SQL, RAG, Forecasting)
3. **Set up Docker**: Follow the docker-containerization-guide.md for containerizing services
4. **Configure your IDE**: Set the Python interpreter to the conda environment

## Support

If you encounter issues not covered here:
1. Check the project's GitHub issues
2. Post in the team WhatsApp/Slack channel
3. Review the official package documentation
4. Contact the team lead who resolved these issues initially

---
*Document maintained by: AC215/E115 Development Team*  
*Last updated: With critical dependency fixes for numpy and skl2onnx compatibility*