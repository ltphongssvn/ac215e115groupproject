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
    assert response.json()["version"] == "2.0.0"

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

def test_timegpt_forecast():
    data = list(np.random.randn(100) * 10 + 100)
    response = client.post("/forecast/generative", json={
        "data": data,
        "model": "timegpt",
        "horizon": 10,
        "mode": "zero-shot"
    })
    assert response.status_code == 200
    result = response.json()
    assert len(result["forecast"]) == 10
    assert result["model_info"]["model"] == "timegpt"

def test_chronos_forecast():
    data = list(np.random.randn(100) * 10 + 100)
    response = client.post("/forecast/generative", json={
        "data": data,
        "model": "chronos",
        "horizon": 10
    })
    assert response.status_code == 200
    assert len(response.json()["forecast"]) == 10

def test_moirai_forecast():
    data = list(np.random.randn(100) * 10 + 100)
    response = client.post("/forecast/generative", json={
        "data": data,
        "model": "moirai",
        "horizon": 10
    })
    assert response.status_code == 200
    assert len(response.json()["forecast"]) == 10

def test_list_models():
    response = client.get("/models")
    assert response.status_code == 200
    assert "generative" in response.json()
    assert "timegpt" in response.json()["generative"]
