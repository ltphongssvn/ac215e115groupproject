#!/usr/bin/env python3
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/integrate_all_data_final.py
"""
Final integration script that merges:
1. Rice prices (4 varieties)
2. Market factors (6 factors: oil, inflation, population, ENSO, fertilizer)
3. Rainfall data (newly generated)
Creates the complete dataset for comprehensive correlation analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directories
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
INTEGRATED_DIR = DATA_DIR / "integrated"
INTEGRATED_DIR.mkdir(parents=True, exist_ok=True)


def load_latest_file(pattern, directory=PROCESSED_DIR):
    """Load the most recent file matching the pattern."""
    files = list(directory.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matching {pattern} in {directory}")
    latest = sorted(files)[-1]
    logger.info(f"Loading: {latest.name}")
    return pd.read_csv(latest)


def main():
    """Main integration function combining all data sources."""
    logger.info("="*60)
    logger.info("FINAL COMPREHENSIVE DATA INTEGRATION")
    logger.info("="*60)

    # Step 1: Load the existing integrated data (rice + market factors)
    logger.info("\n[Step 1/4] Loading existing integrated data...")
    try:
        # First try to load from integrated directory
        df_integrated = load_latest_file("rice_market_integrated_*.csv", INTEGRATED_DIR)
    except FileNotFoundError:
        # If not found, build from scratch
        logger.info("No existing integrated file found. Building from components...")

        # Load rice data
        df_rice = load_latest_file("rice_spreads_*.csv")
        df_rice['Date'] = pd.to_datetime(df_rice['Date'])
        rice_cols = ['Date', 'Thai 5%_price', 'Thai 25%_price', 'Thai A.1_price', 'Vietnamese 5%_price']
        df_rice = df_rice[[col for col in rice_cols if col in df_rice.columns]]

        # Load market factors
        df_market = load_latest_file("market_factors_*.csv")
        df_market['Date'] = pd.to_datetime(df_market['Date'])

        # Merge rice and market factors
        df_integrated = pd.merge(df_rice, df_market, on='Date', how='outer')

    df_integrated['Date'] = pd.to_datetime(df_integrated['Date'])
    logger.info(f"Loaded integrated data: {len(df_integrated)} records")

    # Step 2: Load rainfall data
    logger.info("\n[Step 2/4] Loading rainfall data...")
    df_rainfall = load_latest_file("rainfall_asia_*.csv")
    df_rainfall['Date'] = pd.to_datetime(df_rainfall['Date'])
    logger.info(f"Loaded rainfall data: {len(df_rainfall)} records")

    # Step 3: Merge rainfall with integrated data
    logger.info("\n[Step 3/4] Merging all datasets...")

    # Keep only essential rainfall columns for the final dataset
    rainfall_cols_to_keep = ['Date', 'Asia_Avg_Rainfall_mm', 'Rainfall_Anomaly_pct']

    # Optionally include regional rainfall if desired
    # Uncomment the next line to include all regional data:
    # rainfall_cols_to_keep.extend([col for col in df_rainfall.columns if '_rainfall_mm' in col])

    df_rainfall_subset = df_rainfall[rainfall_cols_to_keep]

    # Perform the merge
    df_final = pd.merge(df_integrated, df_rainfall_subset, on='Date', how='outer')
    df_final = df_final.sort_values('Date').reset_index(drop=True)

    # Step 4: Calculate comprehensive correlations
    logger.info("\n[Step 4/4] Calculating comprehensive correlations...")

    # Define column groups for analysis
    rice_cols = [col for col in df_final.columns if any(x in col for x in ['Thai 5%', 'Thai 25%', 'Thai A.1', 'Vietnamese'])]

    market_factors = [
        'Oil_Dubai_Oman_USD_per_bbl',
        'Inflation_Asia_Avg_pct',
        'Population_Growth_Asia_Avg_pct',
        'Population_Total_Asia_Avg_millions',
        'ENSO_Nino34_Anomaly',
        'Fertilizer_Composite_USD_per_mt',
        'Asia_Avg_Rainfall_mm',
        'Rainfall_Anomaly_pct'
    ]

    # Calculate correlations
    correlations = {}
    for rice_col in rice_cols:
        if rice_col in df_final.columns:
            correlations[rice_col] = {}
            for factor in market_factors:
                if factor in df_final.columns:
                    valid_mask = df_final[rice_col].notna() & df_final[factor].notna()
                    if valid_mask.sum() > 10:
                        corr = df_final.loc[valid_mask, rice_col].corr(df_final.loc[valid_mask, factor])
                        correlations[rice_col][factor] = round(corr, 3)

    # Save the final integrated dataset
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = INTEGRATED_DIR / f"rice_market_rainfall_complete_{timestamp}.csv"
    df_final.to_csv(output_file, index=False)

    # Save comprehensive summary
    summary = {
        'metadata': {
            'creation_date': datetime.now().isoformat(),
            'total_records': len(df_final),
            'date_range': {
                'start': df_final['Date'].min().isoformat(),
                'end': df_final['Date'].max().isoformat()
            },
            'data_sources': {
                'rice_prices': '4 varieties from World Bank Pink Sheet',
                'market_factors': '6 factors (oil, inflation, population, ENSO, fertilizer)',
                'rainfall': 'Climatologically-based synthetic data with ENSO effects'
            }
        },
        'correlations': correlations,
        'data_completeness': {}
    }

    # Calculate completeness for each column
    for col in df_final.columns:
        if col != 'Date':
            completeness = (df_final[col].notna().sum() / len(df_final)) * 100
            summary['data_completeness'][col] = f"{completeness:.1f}%"

    summary_file = INTEGRATED_DIR / f"final_analysis_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Display results
    logger.info("\n" + "="*60)
    logger.info("INTEGRATION COMPLETE - FINAL RESULTS")
    logger.info("="*60)
    logger.info(f"Total variables: {len(df_final.columns)}")
    logger.info(f"Total observations: {len(df_final)}")
    logger.info(f"Date range: {df_final['Date'].min()} to {df_final['Date'].max()}")

    # Show correlation highlights with rainfall
    logger.info("\nRainfall Correlations with Rice Prices:")
    for rice_variety in rice_cols:
        if rice_variety in correlations:
            if 'Asia_Avg_Rainfall_mm' in correlations[rice_variety]:
                rainfall_corr = correlations[rice_variety]['Asia_Avg_Rainfall_mm']
                anomaly_corr = correlations[rice_variety].get('Rainfall_Anomaly_pct', 'N/A')
                logger.info(f"  {rice_variety}:")
                logger.info(f"    Rainfall amount: {rainfall_corr}")
                logger.info(f"    Rainfall anomaly: {anomaly_corr}")

    # Identify strongest correlations overall
    logger.info("\nTop 5 Strongest Correlations:")
    all_correlations = []
    for rice_var, factors in correlations.items():
        for factor, corr_value in factors.items():
            if corr_value is not None:
                all_correlations.append((abs(corr_value), corr_value, rice_var, factor))

    all_correlations.sort(reverse=True)
    for i, (abs_corr, corr, rice_var, factor) in enumerate(all_correlations[:5], 1):
        logger.info(f"  {i}. {rice_var} vs {factor}: {corr:.3f}")

    logger.info(f"\nOutput files:")
    logger.info(f"  Complete dataset: {output_file}")
    logger.info(f"  Analysis summary: {summary_file}")

    logger.info("\nYour dataset is now complete with:")
    logger.info("  • 4 rice price varieties")
    logger.info("  • 6 market factors")
    logger.info("  • Rainfall data with anomalies")
    logger.info("  • Crisis period indicators")
    logger.info("  • Ready for machine learning and advanced analysis")

    return df_final


if __name__ == "__main__":
    main()