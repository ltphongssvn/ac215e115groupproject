# /home/lenovo/code/ltphongssvn/ac215e115groupproject/docs/onboarding/python-verification-guide.md
# Python Environment Verification and Troubleshooting Guide
# Complete checklist to ensure Python tools are properly installed and configured

## Quick Verification Checklist

Run these commands to verify your Python environment is properly configured:

```bash
# 1. Verify Python version (should be 3.12 or higher)
python3 --version

# 2. Check pip is available
pip3 --version

# 3. Verify virtual environment capability
python3 -m venv --help > /dev/null && echo "✓ venv available" || echo "✗ venv not available"

# 4. Check if conda is installed (optional)
command -v conda > /dev/null && echo "✓ conda available: $(conda --version)" || echo "✗ conda not installed"

# 5. Check if uv is installed (optional)
command -v uv > /dev/null && echo "✓ uv available: $(uv --version)" || echo "✗ uv not installed"

# 6. Check if virtualenv is installed (optional)
command -v virtualenv > /dev/null && echo "✓ virtualenv available: $(virtualenv --version)" || echo "✗ virtualenv not installed"
```

## Performance Comparison of Virtual Environment Tools

Based on our testing with the requests package installation:

| Tool | Environment Creation | Package Installation | Total Time | Storage Used |
|------|---------------------|---------------------|------------|--------------|
| venv | ~1 second | ~5-10 seconds | ~11 seconds | ~25 MB |
| conda | ~30 seconds | ~5-10 seconds | ~40 seconds | ~350 MB |
| uv | ~0.5 seconds | ~0.4 seconds | ~1 second | ~25 MB |

### When to Use Each Tool

**Use venv when:**
- You want maximum compatibility and simplicity
- You're working on pure Python projects
- You don't need system-level package management
- You're deploying to environments where only standard Python is available

**Use conda when:**
- Working with data science or scientific computing packages
- You need specific versions of system libraries (CUDA, MKL, etc.)
- You're managing environments with complex non-Python dependencies
- You need to install packages that aren't available on PyPI

**Use uv when:**
- Development speed is a priority
- You're frequently creating and destroying environments
- You're working with modern Python projects
- You want the fastest possible package installation

## Testing Your Environment

After creating a virtual environment with any method, run this comprehensive test:

```bash
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/test_environment.py
# Save this as test_environment.py in your project root

#!/usr/bin/env python3
"""
Comprehensive environment test for AC215/E115 project
Tests that all required packages can be imported and basic functionality works
"""

import sys
import importlib
from typing import List, Tuple

def test_package_import(package_name: str) -> Tuple[bool, str]:
    """Test if a package can be imported and return its version if available."""
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'version not available')
        return True, version
    except ImportError as e:
        return False, str(e)

def main():
    """Run comprehensive environment tests."""
    print("Python Environment Test for AC215/E115 Project")
    print("=" * 50)
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print("=" * 50)
    
    # Core packages to test
    packages = [
        ('fastapi', 'Web Framework'),
        ('uvicorn', 'ASGI Server'),
        ('pydantic', 'Data Validation'),
        ('sqlalchemy', 'Database ORM'),
        ('pandas', 'Data Analysis'),
        ('numpy', 'Numerical Computing'),
        ('sklearn', 'Machine Learning'),
        ('langchain', 'LLM Framework'),
        ('httpx', 'HTTP Client'),
        ('matplotlib', 'Plotting'),
    ]
    
    print("\nPackage Import Tests:")
    print("-" * 50)
    
    all_passed = True
    for package_name, description in packages:
        success, version = test_package_import(package_name)
        status = "✓" if success else "✗"
        if success:
            print(f"{status} {package_name:<15} {version:<15} ({description})")
        else:
            print(f"{status} {package_name:<15} FAILED: {version}")
            all_passed = False
    
    print("-" * 50)
    if all_passed:
        print("\n✓ All packages imported successfully!")
        print("Your environment is properly configured.")
    else:
        print("\n✗ Some packages failed to import.")
        print("Please install missing packages with:")
        print("  pip install -r requirements/dev.txt")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
```

Run the test script:
```bash
python test_environment.py
```

## Clean Up Test Environments

After testing, you can remove the test environments to save space:

```bash
# Remove venv test environment
rm -rf test_venv

# Remove uv test environment  
rm -rf test_uv_env

# Remove conda test environment
conda env remove -n test_ac215 -y

# List remaining environments to confirm cleanup
ls -la | grep -E "test_.*env"
conda env list
```

## Troubleshooting Common Issues

### Issue: "python: command not found"

**Solution:** Use `python3` instead of `python`:
```bash
alias python=python3
echo "alias python=python3" >> ~/.bashrc
```

### Issue: "pip: command not found" 

**Solution:** Install pip or use python3 -m pip:
```bash
sudo apt install python3-pip
# Or use module syntax
python3 -m pip install package_name
```

### Issue: Virtual environment not activating

**Solution:** Check activation script permissions:
```bash
# For venv/virtualenv
chmod +x venv/bin/activate
source venv/bin/activate

# For conda
conda init bash
source ~/.bashrc
conda activate environment_name
```

### Issue: Package conflicts during installation

**Solution:** Create a fresh environment:
```bash
# Remove the problematic environment
rm -rf venv  # or deactivate and remove conda env

# Create new environment
python3 -m venv venv_fresh
source venv_fresh/bin/activate
pip install --upgrade pip
pip install -r requirements/dev.txt
```

### Issue: "error: Microsoft Visual C++ 14.0 is required" (Windows WSL)

**Solution:** Install build tools:
```bash
sudo apt update
sudo apt install build-essential python3-dev
```

### Issue: Conda takes too long to solve environment

**Solution:** Use mamba (faster conda alternative):
```bash
conda install -n base -c conda-forge mamba
mamba create -n project_env python=3.12
mamba install package_name
```

### Issue: SSL Certificate errors

**Solution:** Update certificates and pip:
```bash
pip install --upgrade certifi
# Or if behind corporate proxy
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org package_name
```

## Best Practices for Environment Management

1. **One Environment Per Project:** Never install packages globally. Always use a virtual environment for each project to avoid dependency conflicts.

2. **Document Dependencies:** Always update requirements files when adding new packages:
   ```bash
   pip freeze > requirements/current.txt
   # Then manually update the appropriate requirements file
   ```

3. **Use .gitignore:** Never commit virtual environment directories:
   ```bash
   echo "venv/" >> .gitignore
   echo ".venv/" >> .gitignore
   echo "test_*env/" >> .gitignore
   ```

4. **Regular Updates:** Periodically update packages for security:
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

5. **Environment Variables:** Never hardcode secrets:
   ```bash
   # Always use .env files
   cp .env.example .env
   # Edit .env with your values
   ```

## Verification for Team Collaboration

Before starting work each day:

```bash
# 1. Navigate to project
cd ~/code/ltphongssvn/ac215e115groupproject

# 2. Pull latest changes
git pull origin main

# 3. Activate environment
source venv/bin/activate  # or your chosen method

# 4. Update dependencies if requirements changed
pip install -r requirements/dev.txt

# 5. Verify environment
python test_environment.py

# 6. Start developing
echo "Environment ready for development!"
```

## Additional Resources

- [Python Virtual Environments Documentation](https://docs.python.org/3/tutorial/venv.html)
- [Conda User Guide](https://docs.conda.io/projects/conda/en/latest/user-guide/)
- [uv Documentation](https://github.com/astral-sh/uv)
- [pip Documentation](https://pip.pypa.io/en/stable/)
- [Python Packaging User Guide](https://packaging.python.org/)

## Summary

Your Python development environment is now fully configured with multiple virtual environment options. You have successfully:

1. ✓ Installed Python 3.12+
2. ✓ Set up virtualenv for traditional environment management
3. ✓ Installed conda for scientific computing needs
4. ✓ Configured uv for blazing-fast package management
5. ✓ Created comprehensive requirements files
6. ✓ Tested all three environment creation methods
7. ✓ Documented the entire setup process

You can now choose the most appropriate tool for their specific needs while maintaining consistency through shared requirements files and documentation.

---
*Document maintained by: AC215/E115 Development Team*
*Last verified: September 2025*