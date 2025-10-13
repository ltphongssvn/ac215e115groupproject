# services/rag-orchestrator/tests/test_agentic_rag.py
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
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "agentic-graph-rag"
    assert data["version"] == "2.0.0"

def test_standard_query():
    """Test standard RAG query"""
    response = client.post(
        "/rag/query",
        json={"query": "What are rice prices?", "max_results": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query_type"] == "standard"
    assert "retrieved_documents" in data
    assert data["confidence"] > 0

def test_temporal_query():
    """Test temporal query detection"""
    response = client.post(
        "/rag/query",
        json={"query": "What was rice price last month?", "max_results": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query_type"] == "temporal"
    assert "event_time" in data["metadata"]

def test_rag_query_basic():
    """Test basic RAG query (from test_rag.py)"""
    response = client.post(
        "/rag/query",
        json={"query": "What affects rice prices?", "max_results": 3}
    )
    assert response.status_code == 200
    result = response.json()
    assert "query" in result
    assert "answer" in result
    assert "retrieved_documents" in result

def test_workflow_storage():
    """Test workflow storage"""
    response = client.post(
        "/rag/workflow",
        json={
            "workflow_id": "rice_analysis",
            "steps": [
                {"action": "fetch_data", "params": {"source": "db"}},
                {"action": "analyze", "params": {"method": "trend"}}
            ]
        }
    )
    assert response.status_code == 200
    assert response.json()["workflow_id"] == "rice_analysis"

def test_usage_stats():
    """Test usage statistics"""
    response = client.get("/rag/stats")
    assert response.status_code == 200
    data = response.json()
    assert "usage_patterns" in data
    assert "episodic_buffer_size" in data
