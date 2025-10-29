# services/start_all_microservices.py
import subprocess
import time
import sys
import os

def stop_all_services():
    """Stop all running services"""
    print("\n" + "="*60)
    print("STOPPING ALL SERVICES")
    print("="*60)
    
    services = ["nl-sql-service", "rag-orchestrator", "ts-forecasting"]
    for service in services:
        print(f"Stopping {service}...")
        subprocess.run(["docker", "stop", service], stderr=subprocess.DEVNULL)
        subprocess.run(["docker", "rm", service], stderr=subprocess.DEVNULL)

def start_service(name, port, dockerfile_path, build_context, env_vars=None):
    """Start a Docker service"""
    print(f"\n{'='*60}")
    print(f"Starting {name} on port {port}...")
    print(f"{'='*60}")
    
    image_name = f"{name.lower().replace(' ', '-')}:latest"
    print(f"Building {image_name}...")
    
    build_cmd = ["docker", "build", "-t", image_name, "-f", dockerfile_path, build_context]
    result = subprocess.run(build_cmd, cwd=os.path.dirname(__file__) + "/..")
    
    if result.returncode != 0:
        print(f"❌ Failed to build {name}")
        return False
    
    print(f"Starting container...")
    run_cmd = ["docker", "run", "-d", "--name", name.lower().replace(' ', '-'),
               "-p", f"{port}:{port}"]
    
    if env_vars:
        for key, value in env_vars.items():
            run_cmd.extend(["-e", f"{key}={value}"])
    
    run_cmd.append(image_name)
    result = subprocess.run(run_cmd)
    
    if result.returncode == 0:
        print(f"✅ {name} started on port {port}")
        return True
    else:
        print(f"❌ Failed to start {name}")
        return False

def run_service_tests():
    """Run comprehensive tests for all services"""
    print("\n" + "="*60)
    print("RUNNING SERVICE TESTS")
    print("="*60)
    
    tests = [
        ("NL-SQL Service", "services/nl-sql-service/tests/test_nl_sql.py"),
        ("RAG Orchestrator", "services/rag-orchestrator/tests/test_agentic_rag.py"),
        ("TS Forecasting", "services/ts-forecasting/tests/unit/test_forecasting.py"),
    ]
    
    all_passed = True
    for name, test_path in tests:
        print(f"\nTesting {name}...")
        result = subprocess.run([sys.executable, "-m", "pytest", test_path, "-v"])
        if result.returncode != 0:
            all_passed = False
            print(f"❌ {name} tests failed")
        else:
            print(f"✅ {name} tests passed")
    
    return all_passed

def main():
    stop_all_services()
    
    services = [
        ("NL-SQL Service", 8001, "services/nl-sql-service/Dockerfile", "services/nl-sql-service", 
         {
             "USE_MOCK_LLM": "true",
             "POSTGRES_HOST": "localhost",
             "POSTGRES_PORT": "5432",
             "POSTGRES_USER": "postgres",
             "POSTGRES_PASSWORD": "postgres",
             "POSTGRES_DATABASE": "rice_market"
         }),
        ("RAG Orchestrator", 8002, "services/rag-orchestrator/Dockerfile", "services/rag-orchestrator", None),
        ("TS Forecasting", 8003, "services/ts-forecasting/Dockerfile", ".", None),
    ]
    
    print("\n" + "="*60)
    print("STARTING ALL MICROSERVICES")
    print("="*60)
    
    for name, port, dockerfile, context, env_vars in services:
        start_service(name, port, dockerfile, context, env_vars)
        time.sleep(2)
    
    print("\nWaiting 10 seconds for services to initialize...")
    time.sleep(10)
    
    # Run health checks
    print("\n" + "="*60)
    print("RUNNING HEALTH CHECKS")
    print("="*60)
    health_result = subprocess.run([sys.executable, "tests/test_microservices_health.py"])
    
    # Run comprehensive tests
    tests_passed = run_service_tests()
    
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    if health_result.returncode == 0 and tests_passed:
        print("✅ ALL SERVICES HEALTHY AND TESTS PASSED")
        return 0
    else:
        print("❌ SOME SERVICES OR TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
