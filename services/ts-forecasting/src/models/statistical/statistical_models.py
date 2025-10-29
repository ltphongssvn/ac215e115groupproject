# services/forecasting-service/app/models/statistical_models.py
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class StatisticalForecaster:
    """ARIMA and SARIMA implementations"""
    
    def __init__(self):
        self.model = None
        self.model_fit = None
        
    def fit_arima(self, y: pd.Series, order: tuple = (1, 1, 1)) -> Dict[str, Any]:
        """Fit ARIMA model with auto-parameter selection"""
        try:
            self.model = ARIMA(y, order=order)
            self.model_fit = self.model.fit()
            
            return {
                "model_type": "ARIMA",
                "order": order,
                "aic": self.model_fit.aic,
                "bic": self.model_fit.bic
            }
        except Exception as e:
            logger.error(f"ARIMA fitting failed: {e}")
            raise
    
    def fit_sarima(self, y: pd.Series, order: tuple = (1, 1, 1),
                   seasonal_order: tuple = (1, 1, 1, 12)) -> Dict[str, Any]:
        """Fit SARIMA for seasonal patterns"""
        try:
            self.model = SARIMAX(y, order=order, seasonal_order=seasonal_order)
            self.model_fit = self.model.fit(disp=False)
            
            return {
                "model_type": "SARIMA",
                "order": order,
                "seasonal_order": seasonal_order,
                "aic": self.model_fit.aic,
                "bic": self.model_fit.bic
            }
        except Exception as e:
            logger.error(f"SARIMA fitting failed: {e}")
            raise
    
    def forecast(self, steps: int) -> np.ndarray:
        """Generate forecast for specified horizon"""
        if self.model_fit is None:
            raise ValueError("Model not fitted. Call fit_arima or fit_sarima first.")
        
        forecast = self.model_fit.forecast(steps=steps)
        return forecast.values if isinstance(forecast, pd.Series) else forecast
    
    def get_confidence_intervals(self, steps: int, alpha: float = 0.05) -> Dict[str, np.ndarray]:
        """Get prediction intervals"""
        forecast_result = self.model_fit.get_forecast(steps=steps)
        conf_int = forecast_result.conf_int(alpha=alpha)
        
        return {
            "lower": conf_int.iloc[:, 0].values,
            "upper": conf_int.iloc[:, 1].values
        }
