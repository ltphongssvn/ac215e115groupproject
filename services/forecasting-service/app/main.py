# services/forecasting-service/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import logging
import os

from .data_processing.preprocessor import TimeSeriesPreprocessor
from .models.statistical_models import StatisticalForecaster
from .models.ml_models import ProphetForecaster
from .evaluation.metrics import calculate_metrics

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="Time-Series Forecasting Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ForecastRequest(BaseModel):
    data: List[float]
    dates: Optional[List[str]] = None
    model: str = "arima"
    horizon: int = 30
    frequency: str = "D"

class ForecastResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    forecast: List[float]
    model_info: Dict[str, Any]
    metrics: Optional[Dict[str, float]] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "forecasting", "version": "1.0.0"}

@app.post("/forecast/univariate", response_model=ForecastResponse)
async def forecast_univariate(request: ForecastRequest):
    """Univariate forecasting endpoint"""
    try:
        if request.dates:
            df = pd.DataFrame({
                'date': pd.to_datetime(request.dates),
                'value': request.data
            }).set_index('date')
        else:
            df = pd.DataFrame({'value': request.data})
        
        preprocessor = TimeSeriesPreprocessor(freq=request.frequency)
        df = preprocessor.preprocess(df, 'value')
        
        if request.model == "arima":
            model = StatisticalForecaster()
            model_info = model.fit_arima(df['value'])
            forecast = model.forecast(request.horizon)
            
        elif request.model == "sarima":
            model = StatisticalForecaster()
            model_info = model.fit_sarima(df['value'])
            forecast = model.forecast(request.horizon)
            
        elif request.model == "prophet":
            model = ProphetForecaster()
            model_info = model.fit(df, 'value')
            forecast_df = model.forecast(request.horizon, freq=request.frequency)
            forecast = forecast_df['yhat'].values
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown model: {request.model}")
        
        return ForecastResponse(
            forecast=forecast.tolist(),
            model_info=model_info
        )
        
    except Exception as e:
        logger.error(f"Forecast failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models():
    """List available forecasting models"""
    return {
        "statistical": ["arima", "sarima"],
        "ml": ["prophet", "lstm"],
        "generative": ["timegen", "lag-llama"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
