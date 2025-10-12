# services/ts-forecasting/src/api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.statistical.statistical_models import StatisticalForecaster
from models.ml_models import ProphetForecaster
from models.foundation.timegpt import TimeGPT
from models.foundation.chronos import Chronos
from models.foundation.moirai import MOIRAI
from core.preprocessor import TimeSeriesPreprocessor
from utils.metrics import calculate_metrics

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="Time-Series Forecasting Service", version="2.0.0")

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

class GenerativeForecastRequest(BaseModel):
    data: List[float]
    model: str = "timegpt"
    horizon: int = 30
    mode: str = "zero-shot"
    covariates: Optional[Dict] = None

class ForecastResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    forecast: List[float]
    model_info: Dict[str, Any]
    metrics: Optional[Dict[str, float]] = None

def convert_numpy(obj):
    """Convert numpy arrays to lists recursively"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(item) for item in obj]
    return obj

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ts-forecasting", "version": "2.0.0"}

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

@app.post("/forecast/generative", response_model=ForecastResponse)
async def forecast_generative(request: GenerativeForecastRequest):
    """Generative AI forecasting endpoint"""
    try:
        y = np.array(request.data)
        
        if request.model == "timegpt":
            model = TimeGPT()
            result = model.forecast(y, request.horizon, mode=request.mode, covariates=request.covariates)
            
        elif request.model == "chronos":
            model = Chronos()
            result = model.forecast(y, request.horizon)
            
        elif request.model == "moirai":
            model = MOIRAI()
            result = model.forecast(y, request.horizon)
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown generative model: {request.model}")
        
        result_clean = convert_numpy(result)
        
        return ForecastResponse(
            forecast=result_clean["forecast"],
            model_info=result_clean
        )
        
    except Exception as e:
        logger.error(f"Generative forecast failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models():
    """List available forecasting models"""
    return {
        "statistical": ["arima", "sarima"],
        "ml": ["prophet", "lstm"],
        "generative": ["timegpt", "chronos", "moirai"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
