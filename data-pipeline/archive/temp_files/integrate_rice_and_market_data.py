#!/usr/bin/env python3
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/integrate_rice_and_market_data.py
"""
Integration script to merge rice prices with market factors
Creates comprehensive dataset with 4 rice varieties and 6 market factors
Analyzes correlations and saves integrated dataset
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

def load_latest_file(pattern):
    """Load the most recent file matching pattern."""
    files = list(PROCESSED_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matching {pattern}")
    latest = sorted(files)[-1]
    logger.info(f"Loading: {latest.name}")
    return pd.read_csv(latest)

def main():
    """Main integration function."""
    logger.info("="*60)
    logger.info("RICE AND MARKET FACTORS INTEGRATION")
    logger.info("="*60)
    
    # Load rice price data
    logger.info("\nLoading rice price data...")
    df_rice = load_latest_file("rice_spreads_*.csv")
    df_rice['Date'] = pd.to_datetime(df_rice['Date'])
    
    # Select only price columns
    rice_price_cols = ['Thai 5%_price', 'Thai 25%_price', 'Thai A.1_price', 'Vietnamese 5%_price']
    rice_cols = ['Date'] + [col for col in rice_price_cols if col in df_rice.columns]
    df_rice = df_rice[rice_cols].copy()
    
    # Rename for clarity
    rename_dict = {
        'Thai 5%_price': 'Rice_Thai_5pct',
        'Thai 25%_price': 'Rice_Thai_25pct',
        'Thai A.1_price': 'Rice_Thai_A1',
        'Vietnamese 5%_price': 'Rice_Vietnamese_5pct'
    }
    df_rice.rename(columns=rename_dict, inplace=True)
    
    logger.info(f"Rice data: {len(df_rice)} months, {len(df_rice.columns)-1} varieties")
    
    # Load market factors data
    logger.info("\nLoading market factors data...")
    df_market = load_latest_file("market_factors_*.csv")
    df_market['Date'] = pd.to_datetime(df_market['Date'])
    
    logger.info(f"Market data: {len(df_market)} months, {len(df_market.columns)-1} factors")
    
    # Merge datasets
    logger.info("\nMerging datasets...")
    df_integrated = pd.merge(df_rice, df_market, on='Date', how='outer')
    df_integrated = df_integrated.sort_values('Date').reset_index(drop=True)
    
    # Add derived features
    logger.info("\nAdding derived features...")
    df_integrated['Year'] = df_integrated['Date'].dt.year
    df_integrated['Month'] = df_integrated['Date'].dt.month
    df_integrated['Quarter'] = df_integrated['Date'].dt.quarter
    
    # Add ENSO phase classification
    if 'ENSO_Nino34_Anomaly' in df_integrated.columns:
        df_integrated['ENSO_Phase'] = 'Neutral'
        df_integrated.loc[df_integrated['ENSO_Nino34_Anomaly'] >= 0.5, 'ENSO_Phase'] = 'El Nino'
        df_integrated.loc[df_integrated['ENSO_Nino34_Anomaly'] <= -0.5, 'ENSO_Phase'] = 'La Nina'
    
    # Add crisis period indicators
    df_integrated['Crisis_2008_Financial'] = (
        (df_integrated['Date'] >= '2008-07-01') & 
        (df_integrated['Date'] <= '2009-06-30')
    ).astype(int)
    
    df_integrated['Crisis_2011_Food'] = (
        (df_integrated['Date'] >= '2011-01-01') & 
        (df_integrated['Date'] <= '2012-06-30')
    ).astype(int)
    
    df_integrated['COVID_Period'] = (
        (df_integrated['Date'] >= '2020-03-01') & 
        (df_integrated['Date'] <= '2022-12-31')
    ).astype(int)
    
    df_integrated['Ukraine_Conflict'] = (
        df_integrated['Date'] >= '2022-02-01'
    ).astype(int)
    
    # Calculate correlations
    logger.info("\nCalculating correlations...")
    rice_cols = [col for col in df_integrated.columns if 'Rice_' in col]
    factor_cols = ['Oil_Dubai_Oman_USD_per_bbl', 'Inflation_Asia_Avg_pct',
                   'Population_Growth_Asia_Avg_pct', 'Population_Total_Asia_Avg_millions',
                   'ENSO_Nino34_Anomaly', 'Fertilizer_Composite_USD_per_mt']
    
    correlations = {}
    for rice_col in rice_cols:
        correlations[rice_col] = {}
        for factor_col in factor_cols:
            if factor_col in df_integrated.columns:
                valid_mask = df_integrated[rice_col].notna() & df_integrated[factor_col].notna()
                if valid_mask.sum() > 10:
                    corr = df_integrated.loc[valid_mask, rice_col].corr(
                        df_integrated.loc[valid_mask, factor_col]
                    )
                    correlations[rice_col][factor_col] = round(corr, 3)
    
    # Save integrated dataset
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = INTEGRATED_DIR / f"rice_market_integrated_{timestamp}.csv"
    df_integrated.to_csv(output_file, index=False)
    logger.info(f"\nSaved integrated data to: {output_file}")
    
    # Create summary report
    summary = {
        'metadata': {
            'creation_date': datetime.now().isoformat(),
            'start_date': df_integrated['Date'].min().isoformat(),
            'end_date': df_integrated['Date'].max().isoformat(),
            'total_months': len(df_integrated),
            'rice_varieties': len(rice_cols),
            'market_factors': len([col for col in factor_cols if col in df_integrated.columns])
        },
        'data_coverage': {},
        'correlations': correlations,
        'key_findings': []
    }
    
    # Calculate coverage
    for col in df_integrated.columns:
        if col not in ['Date', 'Year', 'Month', 'Quarter', 'ENSO_Phase']:
            coverage = df_integrated[col].notna().sum() / len(df_integrated) * 100
            summary['data_coverage'][col] = f"{coverage:.1f}%"
    
    # Identify strong correlations
    for rice_variety, corrs in correlations.items():
        for factor, corr_value in corrs.items():
            if abs(corr_value) > 0.7:
                summary['key_findings'].append(
                    f"Strong correlation ({corr_value}) between {rice_variety} and {factor}"
                )
    
    # Save summary
    summary_file = INTEGRATED_DIR / f"integration_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved summary to: {summary_file}")
    
    # Print report
    logger.info("\n" + "="*60)
    logger.info("INTEGRATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Total records: {len(df_integrated)}")
    logger.info(f"Date range: {df_integrated['Date'].min()} to {df_integrated['Date'].max()}")
    logger.info(f"Columns: {len(df_integrated.columns)}")
    
    logger.info("\nData Coverage:")
    for col in rice_cols + factor_cols:
        if col in df_integrated.columns:
            coverage = df_integrated[col].notna().sum() / len(df_integrated) * 100
            logger.info(f"  {col}: {coverage:.1f}%")
    
    logger.info("\nCorrelation Matrix (Rice vs Market Factors):")
    logger.info("-"*60)
    for rice_variety, corrs in correlations.items():
        logger.info(f"\n{rice_variety}:")
        for factor, corr_value in corrs.items():
            strength = "Strong" if abs(corr_value) > 0.7 else "Moderate" if abs(corr_value) > 0.4 else "Weak"
            logger.info(f"  {factor:<40} {corr_value:>7.3f} ({strength})")
    
    if summary['key_findings']:
        logger.info("\nKey Findings:")
        for finding in summary['key_findings']:
            logger.info(f"  • {finding}")
    
    logger.info("\n" + "="*60)
    logger.info("Integration complete! Files saved to: " + str(INTEGRATED_DIR))
    logger.info("="*60)
    
    return df_integrated

if __name__ == "__main__":
    main()
