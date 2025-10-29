# services/ts-forecasting/src/core/preprocessor.py
import pandas as pd
import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class TimeSeriesPreprocessor:
    """Handles missing values, outliers, and data quality for time series"""
    
    def __init__(self, freq: str = 'D'):
        self.freq = freq
        
    def preprocess(self, df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """Main preprocessing pipeline"""
        df = df.copy()
        
        # Ensure datetime index with explicit frequency
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            else:
                df.index = pd.date_range(start='2020-01-01', periods=len(df), freq=self.freq)
        
        # Set explicit frequency to suppress warnings
        if df.index.freq is None:
            df = df.asfreq(self.freq)
        
        df = df.sort_index()
        df = self._handle_missing_values(df, target_col)
        df = self._handle_outliers(df, target_col)
        
        logger.info(f"Preprocessed data shape: {df.shape}")
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """Forward fill then backward fill for missing values"""
        if df[target_col].isna().any():
            missing_count = df[target_col].isna().sum()
            logger.warning(f"Found {missing_count} missing values in {target_col}")
            df[target_col] = df[target_col].ffill().bfill()
        return df
    
    def _handle_outliers(self, df: pd.DataFrame, target_col: str, 
                        threshold: float = 3.0) -> pd.DataFrame:
        """Remove outliers using z-score"""
        z_scores = np.abs((df[target_col] - df[target_col].mean()) / df[target_col].std())
        outliers = z_scores > threshold
        
        if outliers.any():
            logger.warning(f"Found {outliers.sum()} outliers")
            df.loc[outliers, target_col] = np.nan
            df[target_col] = df[target_col].ffill()
        
        return df
    
    def train_test_split(self, df: pd.DataFrame, 
                        test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split time series into train/test"""
        split_idx = int(len(df) * (1 - test_size))
        train = df.iloc[:split_idx]
        test = df.iloc[split_idx:]
        
        logger.info(f"Train: {len(train)}, Test: {len(test)}")
        return train, test
