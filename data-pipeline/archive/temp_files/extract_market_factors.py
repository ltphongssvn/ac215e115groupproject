#!/usr/bin/env python3
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/extract_market_factors.py
"""
Extract and save market factors data from market_drivers.py
Aligns all data to monthly frequency from July 2008 to December 2024
"""

import sys
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import market_drivers module
sys.path.append(str(Path(__file__).parent))
import market_drivers as md

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    """Extract and save all market factors to CSV."""
    logger.info("Starting market factors extraction...")
    
    # Initialize results dataframe with monthly dates
    date_range = pd.date_range(start='2008-07-01', end='2024-12-01', freq='MS')
    df_market = pd.DataFrame({'Date': date_range})
    
    # Track successful loads
    loaded_factors = []
    
    # 1. Load Oil prices
    try:
        logger.info("Loading oil prices...")
        oil_series = md.load_dubai_oman_oil()
        df_market['Oil_Dubai_Oman_USD_per_bbl'] = oil_series.values
        loaded_factors.append('Oil')
        logger.info(f"✓ Oil: {len(oil_series)} months")
    except Exception as e:
        logger.error(f"Failed to load oil data: {e}")
    
    # 2. Load Inflation
    try:
        logger.info("Loading inflation data...")
        inflation_series = md.load_inflation_avg()
        # Align to our date range
        df_market['Inflation_Asia_Avg_pct'] = inflation_series.reindex(df_market['Date']).values
        loaded_factors.append('Inflation')
        logger.info(f"✓ Inflation: {len(inflation_series)} months (interpolated from annual)")
    except Exception as e:
        logger.error(f"Failed to load inflation data: {e}")
    
    # 3. Load Population Growth
    try:
        logger.info("Loading population growth data...")
        pop_growth_series = md.load_population_growth()
        df_market['Population_Growth_Asia_Avg_pct'] = pop_growth_series.reindex(df_market['Date']).values
        loaded_factors.append('Population_Growth')
        logger.info(f"✓ Population Growth: {len(pop_growth_series)} months (interpolated from annual)")
    except Exception as e:
        logger.error(f"Failed to load population growth data: {e}")
    
    # 4. Load Population Total
    try:
        logger.info("Loading population total data...")
        pop_total_series = md.load_population_total()
        # Convert to millions
        pop_total_series = pop_total_series / 1_000_000
        df_market['Population_Total_Asia_Avg_millions'] = pop_total_series.reindex(df_market['Date']).values
        loaded_factors.append('Population_Total')
        logger.info(f"✓ Population Total: {len(pop_total_series)} months (interpolated from annual)")
    except Exception as e:
        logger.error(f"Failed to load population total data: {e}")
    
    # 5. Load ENSO
    try:
        logger.info("Loading ENSO data...")
        enso_series = md.load_nino34()
        df_market['ENSO_Nino34_Anomaly'] = enso_series.values
        loaded_factors.append('ENSO')
        logger.info(f"✓ ENSO: {len(enso_series)} months")
    except Exception as e:
        logger.error(f"Failed to load ENSO data: {e}")
    
    # 6. Load Fertilizer
    try:
        logger.info("Loading fertilizer prices...")
        fertilizer_series = md.load_fertilizer()
        df_market['Fertilizer_Composite_USD_per_mt'] = fertilizer_series.values
        loaded_factors.append('Fertilizer')
        logger.info(f"✓ Fertilizer: {len(fertilizer_series)} months")
    except Exception as e:
        logger.error(f"Failed to load fertilizer data: {e}")
    
    # Save to CSV
    output_file = OUTPUT_DIR / f"market_factors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_market.to_csv(output_file, index=False)
    
    # Summary statistics
    logger.info("\n" + "="*60)
    logger.info("EXTRACTION COMPLETE")
    logger.info("="*60)
    logger.info(f"Successfully loaded {len(loaded_factors)} factors: {', '.join(loaded_factors)}")
    logger.info(f"Date range: {df_market['Date'].min()} to {df_market['Date'].max()}")
    logger.info(f"Total months: {len(df_market)}")
    logger.info(f"Output saved to: {output_file}")
    
    # Data coverage summary
    logger.info("\nData Coverage:")
    for col in df_market.columns:
        if col != 'Date':
            non_null = df_market[col].notna().sum()
            coverage = non_null / len(df_market) * 100
            logger.info(f"  {col}: {non_null}/{len(df_market)} ({coverage:.1f}%)")
    
    return df_market

if __name__ == "__main__":
    main()
