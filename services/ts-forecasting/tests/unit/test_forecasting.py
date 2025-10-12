# services/ts-forecasting/tests/unit/test_forecasting.py
import pytest
from fastapi.testclient import TestClient
import sys
import os
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from api.main import app
import numpy as np

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "ts-forecasting"
    assert response.json()["version"] == "2.0.0"

def test_arima_forecast_with_real_data():
    """Test ARIMA with actual rice price data from CSV"""
    csv_path = "data/integrated/rice_market_rainfall_complete_20251010_062253.csv"
    df = pd.read_csv(csv_path, parse_dates=['Date'])
    
    # Use Thai 5% rice prices with explicit frequency
    data = df['Rice_Thai_5pct'].dropna().tail(100).tolist()
    dates = pd.date_range(start=df['Date'].iloc[-100], periods=100, freq='MS').strftime('%Y-%m-%d').tolist()
    
    response = client.post("/forecast/univariate", json={
        "data": data,
        "dates": dates,
        "model": "arima",
        "horizon": 10,
        "frequency": "MS"
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
