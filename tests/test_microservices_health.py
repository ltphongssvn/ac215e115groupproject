# tests/test_microservices_health.py
import requests
import sys
from typing import Dict, List

def test_nl_sql_service() -> Dict[str, bool]:
    """Test NL-SQL Service health"""
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        return {
            "status": response.status_code == 200,
            "service": "nl-sql-service",
            "port": 8001,
            "response": response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        return {"status": False, "service": "nl-sql-service", "port": 8001, "error": str(e)}

def test_rag_orchestrator() -> Dict[str, bool]:
    """Test RAG Orchestrator health"""
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        return {
            "status": response.status_code == 200,
            "service": "rag-orchestrator",
            "port": 8002,
            "response": response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        return {"status": False, "service": "rag-orchestrator", "port": 8002, "error": str(e)}

def test_ts_forecasting() -> Dict[str, bool]:
    """Test Time-Series Forecasting health"""
    try:
        response = requests.get("http://localhost:8003/health", timeout=5)
        return {
            "status": response.status_code == 200,
            "service": "ts-forecasting",
            "port": 8003,
            "response": response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        return {"status": False, "service": "ts-forecasting", "port": 8003, "error": str(e)}

def run_health_checks() -> int:
    """Run all microservice health checks"""
    print("=" * 60)
    print("MICROSERVICES HEALTH CHECK")
    print("=" * 60)
    
    tests = [
        ("NL-SQL Service", test_nl_sql_service),
        ("RAG Orchestrator", test_rag_orchestrator),
        ("TS Forecasting", test_ts_forecasting)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\nTesting {name}...")
        result = test_func()
        results.append(result)
        
        if result["status"]:
            print(f"✅ {name} - HEALTHY")
            if result.get("response"):
                print(f"   Response: {result['response']}")
        else:
            print(f"❌ {name} - FAILED")
            if result.get("error"):
                print(f"   Error: {result['error']}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    healthy = sum(1 for r in results if r["status"])
    total = len(results)
    
    print(f"Healthy: {healthy}/{total}")
    
    if healthy == total:
        print("✅ ALL SERVICES OPERATIONAL")
        return 0
    else:
        print(f"❌ {total - healthy} SERVICE(S) DOWN")
        return 1

if __name__ == "__main__":
    sys.exit(run_health_checks())
