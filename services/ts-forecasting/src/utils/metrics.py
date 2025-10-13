# services/forecasting-service/app/evaluation/metrics.py
import numpy as np
from typing import Dict

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate MAPE, RMSE, MAE"""
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mape": float(mape)
    }
