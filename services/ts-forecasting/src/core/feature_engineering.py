# services/forecasting-service/app/data_processing/feature_engineering.py
import pandas as pd
import numpy as np
from typing import List

class FeatureEngineer:
    """Create lag features, moving averages, and seasonal components"""
    
    def create_features(self, df: pd.DataFrame, target_col: str, 
                       lags: List[int] = [1, 7, 30]) -> pd.DataFrame:
        """Generate time series features"""
        df = df.copy()
        
        # Lag features
        for lag in lags:
            df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
        
        # Moving averages
        for window in [7, 14, 30]:
            df[f'{target_col}_ma_{window}'] = df[target_col].rolling(window=window).mean()
        
        # Seasonal decomposition features
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        
        # Trend
        df['trend'] = range(len(df))
        
        # Drop rows with NaN from feature creation
        df = df.dropna()
        
        return df
