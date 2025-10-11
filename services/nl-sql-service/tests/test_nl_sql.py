# services/nl-sql-service/tests/test_nl_sql.py
import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)

def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "nl-sql"}

def test_query_endpoint():
    """Test query processing"""
    response = client.post(
        "/query",
        json={"question": "Show me all inventory"}
    )
    assert response.status_code in [200, 400]  # 400 if no DB connection
    assert "question" in response.json()

def test_invalid_query():
    """Test with invalid input"""
    response = client.post("/query", json={})
    assert response.status_code == 422  # Validation error

def test_sql_validation():
    """Test SQL injection prevention"""
    from app.sql_generator_local import SQLGenerator
    gen = SQLGenerator()

    # Should reject dangerous SQL
    assert gen.validate_query("DROP TABLE inventory") == False
    assert gen.validate_query("SELECT * FROM inventory") == True