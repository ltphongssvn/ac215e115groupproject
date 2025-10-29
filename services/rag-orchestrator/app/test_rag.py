# services/rag-orchestrator/app/test_rag.py
import pytest
from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "agentic-graph-rag"

def test_standard_query():
    response = client.post("/rag/query", json={"query": "rice prices"})
    assert response.status_code == 200
    assert response.json()["query_type"] == "standard"

def test_temporal_query():
    response = client.post("/rag/query", json={"query": "rice price last month"})
    assert response.status_code == 200
    assert response.json()["query_type"] == "temporal"

def test_stats():
    response = client.get("/rag/stats")
    assert response.status_code == 200
    assert "usage_patterns" in response.json()
