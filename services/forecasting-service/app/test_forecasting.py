# services/forecasting-service/app/test_forecasting.py
import pytest
from fastapi.testclient import TestClient
from .main import app
import numpy as np

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "forecasting"

def test_arima_forecast():
    data = list(np.random.randn(100) * 10 + 100)
    response = client.post("/forecast/univariate", json={
        "data": data,
        "model": "arima",
        "horizon": 10
    })
    assert response.status_code == 200
    result = response.json()
    assert len(result["forecast"]) == 10
    assert result["model_info"]["model_type"] == "ARIMA"

def test_list_models():
    response = client.get("/models")
    assert response.status_code == 200
    assert "statistical" in response.json()
