# /home/lenovo/code/ltphongssvn/ac215e115groupproject/docs/onboarding/python-setup.md
# Python Development Environment Setup Guide
# AC215/E115 Group Project - Complete Setup Instructions

## Prerequisites

Before setting up the Python environment, ensure you have:
- Ubuntu 24.04 LTS (or compatible Linux distribution)
- Python 3.12 or higher installed
- Git configured with repository access
- At least 5GB free disk space for packages and environments

## Table of Contents
1. [System Python Verification](#system-python-verification)
2. [Virtual Environment Manager Installation](#virtual-environment-manager-installation)
3. [Creating Your Development Environment](#creating-your-development-environment)
4. [Installing Project Dependencies](#installing-project-dependencies)
5. [Environment Verification](#environment-verification)
6. [Common Issues and Solutions](#common-issues-and-solutions)
7. [IDE Configuration](#ide-configuration)

## System Python Verification

First, verify your Python installation meets our requirements:

```bash
# Check Python version (should be 3.12.x or higher)
python3 --version

# Check pip is available
pip3 --version

# Verify Python location
which python3
```

Expected output:
- Python 3.12.3 or higher
- pip 24.0 or higher
- Python located at `/usr/bin/python3`

## Virtual Environment Manager Installation

We support three virtual environment managers. Choose based on your needs:
- **venv**: Built-in, lightweight, perfect for simple Python projects
- **conda**: Best for data science work with complex dependencies
- **uv**: Fastest option, modern tooling, recommended for rapid development

### Option A: Using venv (Pre-installed)

The `venv` module comes with Python 3.12, no additional installation needed.

```bash
# Verify venv is available
python3 -m venv --help
```

### Option B: Installing Conda

Conda excels at managing complex scientific computing environments:

```bash
# Download Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda_installer.sh

# Install Miniconda
bash ~/miniconda_installer.sh -b -p ~/miniconda3

# Initialize conda for your shell
~/miniconda3/bin/conda init bash

# Reload your shell configuration
source ~/.bashrc

# Accept Anaconda Terms of Service
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# Verify installation
conda --version
```

### Option C: Installing uv via Conda

The `uv` package manager offers blazing-fast dependency resolution:

```bash
# Install uv using conda-forge channel
conda install -y -c conda-forge uv

# Verify installation
uv --version
```

### Option D: Installing virtualenv

Traditional virtualenv offers more features than venv:

```bash
# Install using apt (Ubuntu/Debian)
sudo apt update
sudo apt install python3-virtualenv

# Or install using pip
pip3 install --user virtualenv

# Verify installation
virtualenv --version
```

## Creating Your Development Environment

Choose ONE of the following methods based on your preferred tool:

### Method 1: Using venv (Recommended for beginners)

```bash
# Navigate to project directory
cd ~/code/ltphongssvn/ac215e115groupproject

# Create virtual environment
python3 -m venv venv

# Activate the environment
source venv/bin/activate

# Your prompt should now show (venv)
```

### Method 2: Using Conda (Recommended for ML/Data Science)

```bash
# Navigate to project directory
cd ~/code/ltphongssvn/ac215e115groupproject

# Create conda environment with Python 3.12
conda create -n ac215project python=3.12 -y

# Activate the environment
conda activate ac215project

# Your prompt should now show (ac215project)
```

### Method 3: Using uv (Recommended for speed)

```bash
# Navigate to project directory
cd ~/code/ltphongssvn/ac215e115groupproject

# Create virtual environment with uv
uv venv

# Activate the environment
source .venv/bin/activate

# Your prompt should now show (.venv)
```

### Method 4: Using virtualenv

```bash
# Navigate to project directory
cd ~/code/ltphongssvn/ac215e115groupproject

# Create virtual environment
virtualenv -p python3.12 venv

# Activate the environment
source venv/bin/activate

# Your prompt should now show (venv)
```

## Installing Project Dependencies

Once your virtual environment is activated, install the project dependencies:

### For Development Work

```bash
# Install all development dependencies
pip install -r requirements/dev.txt

# This installs:
# - All base packages (FastAPI, pandas, scikit-learn, etc.)
# - Testing tools (pytest, coverage)
# - Code quality tools (black, flake8, mypy)
# - Development tools (jupyter, ipython)
```

### For Production Deployment

```bash
# Install only production dependencies
pip install -r requirements/prod.txt

# This installs:
# - All base packages
# - Production server (gunicorn)
# - Monitoring tools
```

### Using uv for Faster Installation

If you have uv installed, you can use it for much faster package installation:

```bash
# With uv, installations are 10-100x faster
uv pip install -r requirements/dev.txt
```

## Environment Verification

After installation, verify everything is working correctly:

```bash
# Check Python version in environment
python --version

# List installed packages
pip list

# Verify key packages are installed
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
python -c "import pandas; print(f'Pandas {pandas.__version__}')"
python -c "import sklearn; print(f'Scikit-learn {sklearn.__version__}')"

# Test FastAPI installation
python -c "from fastapi import FastAPI; app = FastAPI(); print('FastAPI OK')"

# Test data science stack
python -c "import numpy, pandas, matplotlib; print('Data stack OK')"

# Test ML libraries
python -c "import sklearn, langchain; print('ML stack OK')"
```

## Environment Variables Setup

Configure your environment variables for the project:

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, emacs, code, etc.

# The .env file should contain:
# - API keys (OpenAI, LangChain, etc.)
# - Database connection strings
# - GCP/AWS credentials
# - Application settings
```

## Common Issues and Solutions

### Issue 1: Package Installation Fails

If you encounter errors during package installation:

```bash
# Update pip first
pip install --upgrade pip

# Try installing with no cache
pip install --no-cache-dir -r requirements/dev.txt

# If specific package fails, install it separately
pip install problematic-package --verbose
```

### Issue 2: Conda Environment Not Activating

If conda commands aren't recognized:

```bash
# Ensure conda is initialized
source ~/.bashrc

# Manually activate conda
eval "$(/home/lenovo/miniconda3/bin/conda shell.bash hook)"
```

### Issue 3: Permission Denied Errors

If you get permission errors:

```bash
# Use --user flag for pip
pip install --user -r requirements/dev.txt

# Or fix permissions
chmod +x venv/bin/activate
```

### Issue 4: Wrong Python Version

If Python version is incorrect:

```bash
# For venv, recreate with specific Python
python3.12 -m venv venv --clear

# For conda, update Python in environment
conda activate ac215project
conda install python=3.12
```

## IDE Configuration

### IntelliJ IDEA / PyCharm

1. Open project in IntelliJ IDEA
2. Go to File → Project Structure → SDKs
3. Click + → Add Python SDK → Virtual Environment
4. Select "Existing environment"
5. Browse to: `~/code/ltphongssvn/ac215e115groupproject/venv/bin/python`
6. Apply and OK

### VS Code

1. Open project folder
2. Press Ctrl+Shift+P → "Python: Select Interpreter"
3. Choose the interpreter from your virtual environment:
   - `./venv/bin/python` for venv
   - `~/miniconda3/envs/ac215project/bin/python` for conda

### Jupyter Notebook

To use the project environment in Jupyter:

```bash
# Activate your environment first
source venv/bin/activate  # or conda activate ac215project

# Install ipykernel
pip install ipykernel

# Add environment to Jupyter
python -m ipykernel install --user --name=ac215project --display-name="AC215 Project"

# Start Jupyter
jupyter notebook
```

## Deactivating the Environment

When you're done working:

```bash
# For venv/virtualenv
deactivate

# For conda
conda deactivate
```

## Updating Dependencies

To update packages to latest versions:

```bash
# Update all packages
pip install --upgrade -r requirements/dev.txt

# Update specific package
pip install --upgrade fastapi

# Check for outdated packages
pip list --outdated
```

## Team Collaboration Notes

1. **Always activate the virtual environment** before working on the project
2. **Never commit the virtual environment folders** (venv/, .venv/) to Git
3. **Update requirements files** when adding new packages:
   ```bash
   pip freeze > requirements/current.txt
   # Then manually update the appropriate requirements file
   ```
4. **Document any special setup steps** for your service in its README

## Next Steps

After setting up your environment:

1. Review the project structure in `/docs/architecture/`
2. Check team assignments in `/docs/team/`
3. Read about our microservices design
4. Start developing your assigned service
5. Run tests with `pytest` before committing

## Support

If you encounter issues not covered here:
1. Check the project docs
2. Ask in the team WhatsApp channel
3. Consult the course materials
4. Review the official documentation for specific packages

---
*Last updated: September 2025*
*Maintained by: AC215/E115 Project Team*