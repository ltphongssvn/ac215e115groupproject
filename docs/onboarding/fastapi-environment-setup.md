# /home/lenovo/code/ltphongssvn/ac215e115groupproject/docs/onboarding/fastapi-environment-setup.md
# FastAPI Environment Setup - Complete Onboarding Guide
# Production-ready API Gateway foundation established September 17, 2024

## Executive Summary

On September 17, 2024, our team completed the establishment of a production-ready API gateway foundation for the ERP AI system. This document provides new team members with a complete guide to understanding what was built, why each component matters, and how to replicate this environment on their local machines. The setup includes seven critical layers of infrastructure: authentication, password security, caching, rate limiting, monitoring, security headers, and load testing capabilities.

## Table of Contents

1. [Understanding the Architecture](#understanding-the-architecture)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Installation Guide](#installation-guide)
4. [Verification Process](#verification)
5. [Common Issues and Solutions](#troubleshooting)
6. [How Components Work Together](#integration)
7. [Next Steps for Development](#next-steps)

## Understanding the Architecture {#understanding-the-architecture}

Before diving into installation, it's important to understand what we've built and why. Think of our API gateway as the main entrance to a secure office building. Just as a building entrance needs security guards (authentication), visitor logs (monitoring), controlled access doors (rate limiting), and security cameras (observability), our API gateway needs equivalent digital infrastructure to protect and manage access to our three core microservices: the NL+SQL agent, RAG orchestrator, and time-series forecasting engine.

The FastAPI framework serves as the foundation, like the building's structure itself. On top of this foundation, we've added seven essential layers:

**Authentication Layer (PyJWT)**: This validates that incoming requests come from authorized users. Every request must include a JSON Web Token that proves the user has successfully logged in. Without this, it would be like letting anyone walk into a secure facility without checking their credentials.

**Password Security Layer (passlib with bcrypt)**: When users create accounts, their passwords are transformed through a one-way mathematical function that makes them impossible to reverse-engineer. Even if someone gains access to our database, they cannot retrieve the original passwords.

**Caching Layer (Redis)**: Frequently requested data is stored temporarily in memory for rapid retrieval. When the same rice price data is requested multiple times within five minutes, we serve it from cache rather than regenerating it, dramatically improving response times.

**Rate Limiting Layer (SlowAPI)**: This prevents any single user from overwhelming our services with too many requests. Specifically, our RAG orchestrator limits users to 10 requests per minute, protecting the system from both accidental overuse and deliberate attacks.

**Monitoring Layer (Prometheus)**: Every request that passes through our gateway is measured and recorded. We track response times, error rates, and request volumes, creating a real-time dashboard of system health that enables proactive problem detection.

**Security Headers Layer (secure)**: This adds special instructions to every response that tell web browsers how to handle our content securely. These headers prevent common attacks like clickjacking, cross-site scripting, and content-type confusion.

**Load Testing Layer (Locust)**: This simulates hundreds of users accessing our system simultaneously, allowing us to verify performance under stress before real users encounter problems.

## Prerequisites {#prerequisites}

Before beginning the installation, ensure your development environment meets these requirements. Each requirement serves a specific purpose in maintaining consistency across our development team.

### System Requirements

Your development machine needs Ubuntu 24.04 LTS or a compatible Linux distribution. If you're using Windows, you'll need WSL2 (Windows Subsystem for Linux) properly configured. The Linux environment is essential because our production deployment targets Linux containers, and developing in the same environment prevents compatibility issues.

You'll need at least 2GB of free disk space for package installations and Python 3.12.x specifically. The exact Python version matters because package compatibility can vary between minor versions, and we've tested our entire stack with Python 3.12.

### Environment Preparation

First, verify you have the correct Python version installed. Open your terminal and run:

```bash
python --version
```

You should see Python 3.12.x (where x is any patch version). If you see a different version, you'll need to install Python 3.12 or use a version management tool like pyenv to switch versions.

Next, ensure you have Git configured and can access our repository:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Conda Environment Setup

We use conda for environment management because it provides better isolation than standard Python virtual environments and handles system-level dependencies more effectively. If you don't have conda installed, download and install Miniconda first.

Create and activate the project environment:

```bash
conda create -n test_ac215 python=3.12
conda activate test_ac215
```

The environment name `test_ac215` is our team standard. Using the same environment name ensures that any environment-specific scripts or configurations work consistently across the team.

## Step-by-Step Installation Guide {#installation-guide}

Now we'll install the complete FastAPI environment with all security and operational packages. Follow these steps carefully, understanding what each installation provides for our system.

### Step 1: Clone the Repository

If you haven't already cloned the project repository, do so now:

```bash
git clone https://github.com/ltphongssvn/ac215e115groupproject.git
cd ac215e115groupproject
```

This gets you the latest version of our codebase, including all the requirements files we'll use for installation.

### Step 2: Install Base Requirements

Our base requirements include FastAPI and essential packages that all services need. Install them first:

```bash
pip install -r requirements/base.txt
```

This installation might take several minutes as it includes large packages like pandas, numpy, and scikit-learn. These packages are installed with specific versions to maintain compatibility. For example, we use numpy 1.26.4 instead of 2.x because LangChain, our LLM framework, isn't yet compatible with numpy 2.0's breaking changes.

If you encounter an error about numpy versions, it means the requirements file hasn't been properly updated. The correct version should be numpy==1.26.4, not numpy==2.0.2.

### Step 3: Install API Gateway Security Requirements

Now install the security and operational packages specific to the API gateway:

```bash
pip install -r requirements/api-gateway.txt
```

This installs our seven-layer security infrastructure. Let me explain what's happening during this installation:

Redis (5.0.1) installs the Python client for connecting to Redis servers. Redis itself is a separate service that needs to be running via Docker or system installation. The Python client enables our FastAPI application to store and retrieve cached data.

PyJWT (2.8.0) provides functions for creating and validating JSON Web Tokens. These tokens contain encrypted user information that proves authentication without requiring database lookups on every request.

Passlib with bcrypt (1.7.4) installs password hashing capabilities. The bcrypt algorithm is specifically designed to be computationally expensive, making brute-force attacks impractical.

SlowAPI (0.1.9) adds rate limiting middleware that integrates seamlessly with FastAPI. It tracks request counts per user and automatically returns 429 (Too Many Requests) responses when limits are exceeded.

Prometheus-fastapi-instrumentator (6.1.0) wraps your FastAPI application to automatically collect metrics about every endpoint. These metrics feed into monitoring dashboards and alerting systems.

Secure (0.3.0) provides security headers middleware that adds protective HTTP headers to every response, implementing OWASP security best practices without requiring manual header management.

Locust (2.17.0) installs a complete load testing framework with a web interface. This is a larger installation that includes Flask for the UI and gevent for high-performance concurrent connections.

### Step 4: Verify Installation Success

After installation completes, verify that all packages are properly installed:

```bash
python -c "
import redis
import jwt
import passlib.hash
import slowapi
import prometheus_fastapi_instrumentator
import secure
import locust
print('✓ All FastAPI security packages successfully imported')
print(f'Redis version: {redis.__version__}')
print(f'PyJWT version: {jwt.__version__}')
print(f'Passlib version: {passlib.__version__}')
print('✓ Environment ready for API gateway development')
"
```

This verification script attempts to import each critical package and reports their versions. If any import fails, you'll see an error message indicating which package has issues.

## Verification Process {#verification}

Beyond basic import verification, you should confirm that packages can actually perform their intended functions. This deeper verification ensures that not only are packages installed, but they're properly configured and functional.

### Testing Redis Connectivity

First, ensure Redis server is running. If you're using Docker Compose:

```bash
docker compose up -d redis
```

Then test the Redis Python client:

```python
import redis

# Test Redis connection
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
r.set('test_key', 'test_value')
assert r.get('test_key') == 'test_value'
print("✓ Redis connection and operations working")
```

### Testing JWT Creation and Validation

Test that JWT tokens can be created and validated:

```python
import jwt
from datetime import datetime, timedelta

secret = "test_secret_key_for_development"
payload = {
    "user_id": "123",
    "exp": datetime.utcnow() + timedelta(hours=1)
}

# Create token
token = jwt.encode(payload, secret, algorithm="HS256")
print(f"✓ Created JWT token: {token[:20]}...")

# Validate token
decoded = jwt.decode(token, secret, algorithms=["HS256"])
assert decoded["user_id"] == "123"
print("✓ JWT validation successful")
```

### Testing Password Hashing

Verify password hashing works correctly:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash a password
password = "secure_password_123"
hashed = pwd_context.hash(password)
print(f"✓ Password hashed: {hashed[:20]}...")

# Verify password
assert pwd_context.verify(password, hashed)
assert not pwd_context.verify("wrong_password", hashed)
print("✓ Password verification working correctly")
```

## Common Issues and Solutions {#troubleshooting}

During installation, you might encounter several common issues. Here's how to diagnose and resolve them.

### Issue: ModuleNotFoundError After Installation

If packages appear to install successfully but can't be imported, you're likely in the wrong Python environment.

**Diagnosis**: Check which Python you're using:
```bash
which python
conda info --envs
```

**Solution**: Activate the correct environment:
```bash
conda activate test_ac215
```

### Issue: Version Conflicts During Installation

If pip reports version conflicts, it means packages have incompatible dependency requirements.

**Diagnosis**: Look for error messages mentioning specific version requirements.

**Solution**: Our requirements files have been carefully tested to avoid conflicts. Ensure you're using the latest versions from the repository:
```bash
git pull origin main
pip install --upgrade -r requirements/base.txt -r requirements/api-gateway.txt
```

### Issue: Redis Connection Errors

If Redis connection fails, the Redis server might not be running.

**Diagnosis**: Try connecting to Redis directly:
```bash
redis-cli ping
```

**Solution**: Start Redis using Docker:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### Issue: Memory Errors During Installation

Large packages like pandas and scikit-learn require significant memory during installation.

**Solution**: Close other applications to free memory, or install packages individually:
```bash
pip install pandas==2.2.3
pip install scikit-learn==1.5.2
```

## How Components Work Together {#integration}

Understanding how these packages integrate helps you write effective API gateway code. Let me walk you through a complete example that demonstrates the integration pattern.

```python
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/api-gateway/main.py
# Complete FastAPI gateway with all security layers integrated

from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from passlib.context import CryptContext
import redis
import jwt
import secure
from datetime import datetime, timedelta
from typing import Optional

# Initialize FastAPI with metadata
app = FastAPI(
    title="ERP AI API Gateway",
    description="Secure gateway for rice market intelligence services",
    version="1.0.0"
)

# Layer 1: Password Security - Configure bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Layer 2: Authentication - Configure JWT token handling
SECRET_KEY = "your-secret-key-from-environment"  # Load from environment in production
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Layer 3: Caching - Connect to Redis
redis_client = redis.Redis(
    host='localhost', 
    port=6379, 
    decode_responses=True,
    connection_pool_max_connections=50
)

# Layer 4: Rate Limiting - Configure request limits
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Layer 5: Monitoring - Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Layer 6: Security Headers - Configure OWASP headers
secure_headers = secure.SecureHeaders(
    csp="default-src 'self'",
    hsts=secure.HSTS(max_age=31536000, include_subdomains=True),
    referrer="strict-origin-when-cross-origin",
    permissions_policy="geolocation=(), microphone=(), camera=()"
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to every response"""
    response = await call_next(request)
    secure_headers.framework.fastapi(response)
    return response

# Helper function to create JWT tokens
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT token with expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Helper function to verify JWT tokens
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate JWT token and return user info"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except jwt.PyJWTError:
        raise credentials_exception

# Example endpoint with all security layers
@app.get("/api/v1/nl-query")
@limiter.limit("10/minute")  # Rate limiting
async def natural_language_query(
    request: Request,
    query: str,
    current_user: str = Depends(get_current_user)  # Authentication required
):
    """
    Process natural language query with caching.
    This endpoint demonstrates all security layers in action.
    """
    # Check cache first
    cache_key = f"nl_query:{current_user}:{query}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return {"result": cached_result, "cached": True}
    
    # Process query (placeholder for actual NL processing)
    result = f"Processed query: {query} for user: {current_user}"
    
    # Cache result for 5 minutes (300 seconds)
    redis_client.setex(cache_key, 300, result)
    
    return {"result": result, "cached": False}

# Health check endpoint (no authentication required)
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    # Layer 7: Load testing configuration
    # Run with: locust -f tests/locustfile.py --host=http://localhost:8000
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

This integration example shows how each security layer protects your API. The password hashing ensures stored credentials are secure. JWT authentication validates each request. Redis caching improves performance. Rate limiting prevents abuse. Prometheus monitoring tracks everything. Security headers protect against browser-based attacks. And Locust testing validates that all these layers work together under load.

## Next Steps for Development {#next-steps}

With your FastAPI environment fully configured, you're ready to begin actual API gateway development. Here's what comes next in your journey.

### Creating Your First Secure Endpoint

Start by implementing one complete endpoint that uses all security layers. Pick a simple use case like retrieving user profile information. This helps you understand the full request lifecycle through all security layers.

### Setting Up Development Workflow

Configure your IDE to recognize the test_ac215 environment. In VS Code, press Ctrl+Shift+P, select "Python: Select Interpreter", and choose the test_ac215 environment. This ensures code completion and error checking work correctly.

### Writing Load Tests

Create a Locust test file that simulates real user behavior:

```python
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/tests/locustfile.py
from locust import HttpUser, task, between

class APIGatewayUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def test_nl_query(self):
        self.client.get("/api/v1/nl-query?query=show rice prices")
    
    @task
    def test_health(self):
        self.client.get("/health")
```

Run tests with: `locust -f tests/locustfile.py --host=http://localhost:8000`

### Connecting to Backend Services

Your API gateway needs to forward requests to the three backend services. Implement service discovery and request forwarding patterns that maintain authentication while efficiently routing requests.

### Monitoring and Debugging

Access Prometheus metrics at `http://localhost:8000/metrics` to see real-time performance data. Use this information to identify bottlenecks and optimize performance.

## Conclusion

You now have a complete, production-ready FastAPI environment with comprehensive security and operational capabilities. This foundation represents dozens of hours of careful configuration and testing, compressed into a straightforward installation process you can complete in under an hour.

Remember that this environment is the foundation, not the final product. The actual API gateway implementation, with its specific business logic for routing requests to your NL+SQL, RAG, and forecasting services, still needs to be built on top of this foundation. However, with authentication, caching, rate limiting, monitoring, security headers, and load testing all in place, you can focus on implementing business value rather than wrestling with infrastructure concerns.

When you encounter issues or have questions, refer back to this guide and the detailed comments in the requirements files. The team has invested significant effort in documentation to ensure knowledge transfer and consistency across all development environments.

---
*Document created: September 17, 2024*  
*Last updated: September 17, 2024*  
*Maintainer: AC215/E115 Development Team*