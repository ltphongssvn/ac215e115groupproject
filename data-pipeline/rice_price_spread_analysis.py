#!/usr/bin/env python3
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/rice_price_spread_analysis.py
"""
Rice Price Spread Analysis Script for ERP AI System Data Pipeline
Downloads World Bank Pink Sheet data and computes rice grade spreads.
Analyzes Thai 5%, Thai 25%, Thai A.1, and Vietnamese 5% rice prices.
Prepares clean commodity price data for BigQuery data warehouse ingestion (Milestone 2.6).
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from typing import Dict, Tuple, Optional, List
import logging
import json
import hashlib

# Configure logging with clear formatting for pipeline monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for World Bank data source
PINKSHEET_XLSX_URL = (
    "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021"
    "/related/CMO-Historical-Data-Monthly.xlsx"
)

# Project directory structure following the established data organization pattern
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw" / "external_rice_market" / "worldbank_pink_sheet"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
INTERIM_DATA_DIR = DATA_DIR / "interim"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
INTERIM_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Rice series column mappings based on World Bank Pink Sheet structure
RICE_SERIES_MAPPING = {
    "Thai 5%": "Rice, Thai 5%",
    "Thai 25%": "Rice, Thai 25%", 
    "Thai A.1": "Rice, Thai A-1",
    "Vietnamese 5%": "Rice, Vietnamese 5%"
}

def download_pink_sheet_data(force_download: bool = False) -> Path:
    """
    Downloads the World Bank Pink Sheet Excel file containing commodity prices.
    This function implements a simple caching strategy to avoid unnecessary downloads,
    which is important for efficient pipeline operation and respecting the data source.
    
    The downloaded file is stored in the raw data directory with a date stamp,
    allowing us to track different versions of the source data over time.
    
    Args:
        force_download: If True, downloads even if today's file already exists
        
    Returns:
        Path to the downloaded Excel file
    """
    # Create filename with date for version tracking and audit trail
    today_str = datetime.now().strftime("%Y%m%d")
    excel_filename = f"CMO-Historical-Data-Monthly_{today_str}.xlsx"
    excel_path = RAW_DATA_DIR / excel_filename
    
    # Check cache to avoid redundant downloads
    if excel_path.exists() and not force_download:
        logger.info(f"Using cached Pink Sheet data: {excel_path}")
        return excel_path
    
    logger.info(f"Downloading Pink Sheet data from World Bank...")
    logger.info(f"URL: {PINKSHEET_XLSX_URL}")
    
    try:
        # Use appropriate headers to ensure successful download
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(PINKSHEET_XLSX_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save the raw Excel file to our data lake structure
        with open(excel_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded Pink Sheet data to: {excel_path}")
        logger.info(f"File size: {len(response.content) / 1024 / 1024:.2f} MB")
        
        return excel_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download Pink Sheet data: {e}")
        raise

def extract_rice_price_data(excel_path: Path, start_year: int = 2022) -> pd.DataFrame:
    """
    Extracts rice price data from the World Bank Pink Sheet Excel file.
    
    This function handles the complexities of the Pink Sheet format, which can vary
    slightly between releases. It searches for the correct sheet and columns,
    making the pipeline robust to minor format changes.
    
    Args:
        excel_path: Path to the Pink Sheet Excel file
        start_year: Year from which to start extracting data (for CLI flexibility)
        
    Returns:
        DataFrame with rice price time series data
    """
    logger.info(f"Extracting rice price data from: {excel_path}")
    logger.info(f"Filtering for data from {start_year} onwards")
    
    try:
        # Read Excel file to explore available sheets
        xls = pd.ExcelFile(excel_path)
        logger.info(f"Available sheets in Pink Sheet: {xls.sheet_names}")
        
        # Find the correct data sheet (World Bank may use different naming)
        sheet_name = None
        potential_sheet_names = ['Monthly Prices', 'Monthly', 'Prices', 'Data']
        for name in potential_sheet_names:
            if name in xls.sheet_names:
                sheet_name = name
                break
        
        # Fallback to first sheet if no match found
        if not sheet_name and len(xls.sheet_names) > 0:
            sheet_name = xls.sheet_names[0]
            logger.warning(f"Using fallback sheet: {sheet_name}")
        
        # Read data - Pink Sheet typically has headers around row 4-5
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=4)
        
        # Identify the date column (can have various names)
        date_column_candidates = ['Period', 'Date', 'Month', 'TIME', 'Time']
        date_col = None
        
        for col in date_column_candidates:
            if col in df.columns:
                date_col = col
                break
        
        # Secondary check: find column with datetime data type
        if not date_col:
            for col in df.columns:
                if df[col].dtype == 'datetime64[ns]' or 'date' in str(col).lower():
                    date_col = col
                    break
        
        if not date_col:
            raise ValueError("Could not identify date column in Pink Sheet data")
        
        logger.info(f"Using date column: {date_col}")
        logger.info(f"Total columns available: {len(df.columns)}")
        
        # Standardize date column name
        df = df.rename(columns={date_col: 'Date'})
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Apply date filter based on start_year parameter
        df = df[df['Date'] >= f'{start_year}-01-01']
        
        # Find rice price columns using our mapping
        rice_columns_found = {}
        for label, col_pattern in RICE_SERIES_MAPPING.items():
            if col_pattern in df.columns:
                rice_columns_found[label] = col_pattern
            else:
                # Try flexible matching for column variations
                for col in df.columns:
                    if col_pattern.lower() in str(col).lower():
                        rice_columns_found[label] = col
                        break
        
        logger.info(f"Identified rice price columns: {rice_columns_found}")
        
        if not rice_columns_found:
            logger.error("No rice price columns found!")
            logger.info(f"Sample of available columns: {list(df.columns[:20])}")
            raise ValueError("Required rice price columns not found in data")
        
        # Select only date and rice price columns
        columns_to_keep = ['Date'] + list(rice_columns_found.values())
        df = df[columns_to_keep]
        
        # Rename to standardized column names
        rename_dict = {v: k for k, v in rice_columns_found.items()}
        df = df.rename(columns=rename_dict)
        
        # Clean data: remove rows where all prices are missing
        price_cols = [col for col in df.columns if col != 'Date']
        df = df.dropna(subset=price_cols, how='all')
        
        # Sort chronologically
        df = df.sort_values('Date')
        
        logger.info(f"Extracted {len(df)} months of rice price data")
        logger.info(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        logger.info(f"Columns: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to extract rice price data: {e}")
        raise

def compute_price_spreads(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes price spreads between Thai 5% (benchmark) and other rice varieties.
    
    Thai 5% is used as the benchmark because it's the most liquid and widely
    traded rice grade. The spreads help traders and analysts understand:
    - Quality premiums/discounts between different rice grades
    - Market dynamics and arbitrage opportunities
    - Regional price differences (Thai vs Vietnamese markets)
    
    Args:
        df: DataFrame with rice price data
        
    Returns:
        Tuple of (absolute spreads in USD/mt, percentage spreads)
    """
    logger.info("Computing rice price spreads with Thai 5% as benchmark...")
    
    # Initialize dataframes for different spread types
    spreads_df = df[['Date']].copy()
    spreads_pct_df = df[['Date']].copy()
    
    # Verify benchmark price exists
    if 'Thai 5%' not in df.columns:
        raise ValueError("Thai 5% benchmark price not found in data")
    
    base_price = df['Thai 5%']
    
    # Calculate spreads for each variety
    varieties = ['Thai 25%', 'Thai A.1', 'Vietnamese 5%']
    
    for variety in varieties:
        if variety in df.columns:
            # Absolute spread in USD per metric ton
            # Positive values mean Thai 5% is more expensive (premium)
            spreads_df[f'{variety}_spread_usd'] = base_price - df[variety]
            
            # Percentage spread relative to Thai 5% price
            # Useful for understanding relative price movements
            spreads_pct_df[f'{variety}_spread_pct'] = (
                (base_price - df[variety]) / base_price * 100
            )
            
            # Log statistics for monitoring
            latest_spread = spreads_df[f'{variety}_spread_usd'].iloc[-1]
            avg_spread = spreads_df[f'{variety}_spread_usd'].mean()
            logger.info(f"{variety}: Latest spread=${latest_spread:.2f}/mt, Average=${avg_spread:.2f}/mt")
        else:
            logger.warning(f"Variety {variety} not found in data - skipping")
    
    # Include original prices for reference and analysis
    for col in df.columns:
        if col != 'Date':
            spreads_df[f'{col}_price'] = df[col]
            spreads_pct_df[f'{col}_price'] = df[col]
    
    logger.info(f"Computed spreads for {len(spreads_df)} time periods")
    
    return spreads_df, spreads_pct_df

def prepare_for_bigquery(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares the rice price spread data for BigQuery data warehouse ingestion.
    
    This function formats the data according to BigQuery best practices and adds
    metadata required for the data pipeline (Milestone 2.6). The output is
    structured to support efficient querying and integration with the broader
    ERP AI system.
    
    Key preparations include:
    - Adding metadata for data lineage and versioning
    - Creating partitioning columns for BigQuery performance
    - Generating unique identifiers for idempotent loading
    - Ensuring proper data types for BigQuery compatibility
    
    Args:
        df: DataFrame with computed spreads
        
    Returns:
        DataFrame ready for BigQuery ingestion via Pub/Sub or batch loading
    """
    logger.info("Preparing data for BigQuery data warehouse...")
    
    bq_df = df.copy()
    
    # Add metadata columns for data governance and lineage tracking
    bq_df['ingestion_timestamp'] = datetime.now()
    bq_df['data_source'] = 'worldbank_pink_sheet'
    bq_df['data_version'] = '1.0.0'
    bq_df['pipeline_name'] = 'rice_price_spread_analysis'
    
    # Generate unique record ID for each row
    # This ensures idempotent loads - duplicate runs won't create duplicate records
    bq_df['record_id'] = bq_df.apply(
        lambda row: hashlib.md5(
            f"{row['Date']}{row.get('Thai 5%_price', '')}".encode()
        ).hexdigest(),
        axis=1
    )
    
    # Ensure proper date formatting for BigQuery
    bq_df['Date'] = pd.to_datetime(bq_df['Date']).dt.date
    
    # Replace NaN with None for BigQuery NULL representation
    bq_df = bq_df.where(pd.notnull(bq_df), None)
    
    # Add partitioning columns for efficient BigQuery queries
    # These columns enable partition pruning for faster, cheaper queries
    bq_df['year'] = pd.to_datetime(bq_df['Date']).dt.year
    bq_df['month'] = pd.to_datetime(bq_df['Date']).dt.month
    bq_df['quarter'] = pd.to_datetime(bq_df['Date']).dt.quarter
    
    # Add calculated fields useful for analysis
    bq_df['day_of_week'] = pd.to_datetime(bq_df['Date']).dt.dayofweek
    bq_df['week_of_year'] = pd.to_datetime(bq_df['Date']).dt.isocalendar().week
    
    logger.info(f"Prepared {len(bq_df)} records for BigQuery")
    logger.info(f"Schema includes {len(bq_df.columns)} columns")
    logger.info(f"Columns: {list(bq_df.columns)}")
    
    return bq_df

def create_visualizations(spreads_df: pd.DataFrame, spreads_pct_df: pd.DataFrame,
                         output_dir: Path = PROCESSED_DATA_DIR) -> Dict[str, Path]:
    """
    Creates professional visualization charts for rice price spread analysis.
    
    These visualizations serve multiple purposes:
    1. Quick visual analysis for traders and analysts
    2. Report generation for stakeholders
    3. Monitoring dashboards for the ERP system
    
    The charts are designed to be clear and informative, suitable for both
    technical and business audiences.
    
    Args:
        spreads_df: DataFrame with absolute spreads
        spreads_pct_df: DataFrame with percentage spreads
        output_dir: Directory to save chart files
        
    Returns:
        Dictionary mapping chart types to their file paths
    """
    logger.info("Creating visualization charts...")
    
    # Use a professional style for the charts
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Create comprehensive analysis figure with multiple subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Rice Market Price Spread Analysis - World Bank Pink Sheet Data', 
                 fontsize=16, fontweight='bold')
    
    # Subplot 1: Absolute spreads time series
    ax1 = axes[0, 0]
    for col in spreads_df.columns:
        if 'spread_usd' in col:
            variety = col.replace('_spread_usd', '')
            ax1.plot(spreads_df['Date'], spreads_df[col], 
                    label=variety, linewidth=2, alpha=0.8)
    
    ax1.set_title('Rice Grade Spreads vs Thai 5% Benchmark (USD/mt)')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price Spread (USD/mt)')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5, linewidth=0.5)
    
    # Subplot 2: Percentage spreads for relative comparison
    ax2 = axes[0, 1]
    for col in spreads_pct_df.columns:
        if 'spread_pct' in col:
            variety = col.replace('_spread_pct', '')
            ax2.plot(spreads_pct_df['Date'], spreads_pct_df[col], 
                    label=variety, linewidth=2, alpha=0.8)
    
    ax2.set_title('Relative Price Spreads (% of Thai 5% Price)')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Spread (%)')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5, linewidth=0.5)
    
    # Subplot 3: Actual rice prices for context
    ax3 = axes[1, 0]
    for col in spreads_df.columns:
        if '_price' in col and 'spread' not in col:
            variety = col.replace('_price', '')
            ax3.plot(spreads_df['Date'], spreads_df[col], 
                    label=variety, linewidth=2, alpha=0.8)
    
    ax3.set_title('Rice Prices by Grade (USD/mt)')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Price (USD/mt)')
    ax3.legend(loc='best')
    ax3.grid(True, alpha=0.3)
    
    # Subplot 4: Distribution analysis with box plots
    ax4 = axes[1, 1]
    spread_cols = [col for col in spreads_df.columns if 'spread_usd' in col]
    spread_data = [spreads_df[col].dropna() for col in spread_cols]
    spread_labels = [col.replace('_spread_usd', '') for col in spread_cols]
    
    bp = ax4.boxplot(spread_data, labels=spread_labels, patch_artist=True)
    
    # Color the box plots for better visualization
    colors = ['lightblue', 'lightgreen', 'lightcoral']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax4.set_title('Spread Distribution Statistics')
    ax4.set_ylabel('Spread (USD/mt)')
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5, linewidth=0.5)
    
    plt.tight_layout()
    
    # Save the comprehensive analysis chart
    timestamp = datetime.now().strftime('%Y%m%d')
    main_chart_path = output_dir / f"rice_spread_analysis_{timestamp}.png"
    plt.savefig(main_chart_path, dpi=300, bbox_inches='tight')
    logger.info(f"Saved main analysis chart to: {main_chart_path}")
    
    # Create focused percentage spread chart for detailed analysis
    plt.figure(figsize=(12, 6))
    
    for col in spreads_pct_df.columns:
        if 'spread_pct' in col:
            variety = col.replace('_spread_pct', '')
            plt.plot(spreads_pct_df['Date'], spreads_pct_df[col], 
                    label=variety, linewidth=2.5, marker='o', markersize=2, alpha=0.8)
    
    plt.title('Rice Price Spreads as Percentage of Thai 5% Benchmark Price', 
             fontsize=14, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Spread (% of Thai 5% Price)', fontsize=12)
    plt.legend(loc='best', frameon=True, shadow=True)
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='black', linestyle='--', alpha=0.5, linewidth=1)
    
    # Add shaded regions for significant spread levels
    plt.axhspan(-5, 5, alpha=0.1, color='gray', label='Normal Range')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    pct_chart_path = output_dir / f"rice_percentage_spreads_{timestamp}.png"
    plt.savefig(pct_chart_path, dpi=300, bbox_inches='tight')
    logger.info(f"Saved percentage spreads chart to: {pct_chart_path}")
    
    plt.close('all')  # Clean up matplotlib memory
    
    return {
        'main_chart': main_chart_path,
        'percentage_chart': pct_chart_path
    }

def save_processed_data(spreads_df: pd.DataFrame, spreads_pct_df: pd.DataFrame,
                        bq_ready_df: pd.DataFrame) -> Dict[str, Path]:
    """
    Saves processed data in multiple formats for different consumption patterns.
    
    This function creates outputs suitable for:
    - Batch loading into BigQuery (CSV)
    - Streaming via Pub/Sub to BigQuery (JSON)
    - Analysis in pandas or other tools (CSV)
    - Integration with other microservices (JSON)
    
    Args:
        spreads_df: DataFrame with absolute spreads
        spreads_pct_df: DataFrame with percentage spreads
        bq_ready_df: DataFrame formatted for BigQuery
        
    Returns:
        Dictionary mapping output types to file paths
    """
    logger.info("Saving processed data files...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save absolute spreads for analysis
    spreads_path = PROCESSED_DATA_DIR / f"rice_spreads_usd_{timestamp}.csv"
    spreads_df.to_csv(spreads_path, index=False)
    logger.info(f"Saved absolute spreads: {spreads_path}")
    
    # Save percentage spreads for relative analysis
    spreads_pct_path = PROCESSED_DATA_DIR / f"rice_spreads_pct_{timestamp}.csv"
    spreads_pct_df.to_csv(spreads_pct_path, index=False)
    logger.info(f"Saved percentage spreads: {spreads_pct_path}")
    
    # Save BigQuery-ready CSV for batch loading
    bq_csv_path = PROCESSED_DATA_DIR / f"rice_spreads_bigquery_{timestamp}.csv"
    bq_ready_df.to_csv(bq_csv_path, index=False)
    logger.info(f"Saved BigQuery CSV: {bq_csv_path}")
    
    # Save JSON for Pub/Sub streaming ingestion
    bq_json_path = PROCESSED_DATA_DIR / f"rice_spreads_bigquery_{timestamp}.jsonl"
    
    # Use JSON Lines format (one JSON object per line) for streaming
    # This format is optimal for Pub/Sub message processing
    bq_ready_df.to_json(bq_json_path, orient='records', lines=True, date_format='iso')
    logger.info(f"Saved BigQuery JSON Lines: {bq_json_path}")
    
    return {
        'spreads_csv': spreads_path,
        'spreads_pct_csv': spreads_pct_path,
        'bigquery_csv': bq_csv_path,
        'bigquery_jsonl': bq_json_path
    }

def generate_summary_statistics(spreads_df: pd.DataFrame, spreads_pct_df: pd.DataFrame) -> Dict:
    """
    Generates comprehensive summary statistics for the analysis.
    
    These statistics are used for:
    - Monitoring data quality and completeness
    - Feeding into machine learning models for forecasting
    - Creating executive dashboards
    - Triggering alerts when spreads exceed thresholds
    
    Args:
        spreads_df: DataFrame with absolute spreads
        spreads_pct_df: DataFrame with percentage spreads
        
    Returns:
        Dictionary with detailed statistics and metrics
    """
    logger.info("Generating summary statistics...")
    
    summary = {
        'analysis_metadata': {
            'timestamp': datetime.now().isoformat(),
            'pipeline_version': '1.0.0',
            'data_source': 'World Bank Pink Sheet'
        },
        'data_coverage': {
            'start_date': str(spreads_df['Date'].min()),
            'end_date': str(spreads_df['Date'].max()),
            'total_periods': len(spreads_df),
            'missing_data_points': int(spreads_df.isnull().sum().sum())
        },
        'absolute_spreads_usd': {},
        'percentage_spreads': {},
        'price_levels': {},
        'market_insights': {}
    }
    
    # Calculate detailed statistics for absolute spreads
    for col in spreads_df.columns:
        if 'spread_usd' in col:
            variety = col.replace('_spread_usd', '')
            spread_series = spreads_df[col].dropna()
            
            summary['absolute_spreads_usd'][variety] = {
                'mean': float(spread_series.mean()),
                'median': float(spread_series.median()),
                'std_deviation': float(spread_series.std()),
                'min': float(spread_series.min()),
                'max': float(spread_series.max()),
                'quartile_25': float(spread_series.quantile(0.25)),
                'quartile_75': float(spread_series.quantile(0.75)),
                'latest': float(spread_series.iloc[-1]) if len(spread_series) > 0 else None,
                'trend': 'increasing' if spread_series.iloc[-1] > spread_series.mean() else 'decreasing'
            }
    
    # Calculate percentage spread statistics
    for col in spreads_pct_df.columns:
        if 'spread_pct' in col:
            variety = col.replace('_spread_pct', '')
            pct_series = spreads_pct_df[col].dropna()
            
            summary['percentage_spreads'][variety] = {
                'mean': float(pct_series.mean()),
                'median': float(pct_series.median()),
                'std_deviation': float(pct_series.std()),
                'min': float(pct_series.min()),
                'max': float(pct_series.max()),
                'latest': float(pct_series.iloc[-1]) if len(pct_series) > 0 else None,
                'volatility_coefficient': float(pct_series.std() / pct_series.mean()) if pct_series.mean() != 0 else None
            }
    
    # Calculate price level statistics
    for col in spreads_df.columns:
        if '_price' in col and 'spread' not in col:
            variety = col.replace('_price', '')
            price_series = spreads_df[col].dropna()
            
            summary['price_levels'][variety] = {
                'mean': float(price_series.mean()),
                'median': float(price_series.median()),
                'min': float(price_series.min()),
                'max': float(price_series.max()),
                'latest': float(price_series.iloc[-1]) if len(price_series) > 0 else None,
                'price_range': float(price_series.max() - price_series.min()),
                'year_over_year_change': None  # Could be calculated if we have enough historical data
            }
    
    # Generate market insights based on the statistics
    thai_25_spread = summary['absolute_spreads_usd'].get('Thai 25%', {})
    viet_spread = summary['absolute_spreads_usd'].get('Vietnamese 5%', {})
    
    summary['market_insights'] = {
        'thai_market_premium': thai_25_spread.get('mean', 0) > 0,
        'vietnamese_competitiveness': viet_spread.get('mean', 0) < thai_25_spread.get('mean', 0),
        'spread_volatility': 'high' if thai_25_spread.get('std_deviation', 0) > 50 else 'normal',
        'recommendation': 'monitor_closely' if abs(thai_25_spread.get('latest', 0)) > 100 else 'stable'
    }
    
    # Save summary to JSON for programmatic access
    summary_path = PROCESSED_DATA_DIR / f"analysis_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved summary statistics: {summary_path}")
    
    # Log key findings for immediate visibility
    logger.info("\n" + "="*60)
    logger.info("KEY MARKET FINDINGS")
    logger.info("="*60)
    for variety, stats in summary['absolute_spreads_usd'].items():
        logger.info(f"{variety}:")
        logger.info(f"  - Current spread: ${stats['latest']:.2f}/mt")
        logger.info(f"  - Average spread: ${stats['mean']:.2f}/mt")
        logger.info(f"  - Trend: {stats['trend']}")
    
    return summary

def main():
    """
    Main orchestration function for the rice price spread analysis pipeline.
    
    This function coordinates all the data processing steps and ensures proper
    error handling and logging throughout the pipeline execution. It's designed
    to be run as part of the larger ERP AI system's data ingestion pipeline
    (Milestone 2.6) or as a standalone analysis tool.
    """
    parser = argparse.ArgumentParser(
        description='Rice Price Spread Analysis Pipeline for ERP AI System',
        epilog='This tool downloads World Bank Pink Sheet data and prepares it for BigQuery ingestion.'
    )
    parser.add_argument('--start-year', type=int, default=2022,
                       help='Start year for analysis (default: 2022). Use earlier years for historical analysis.')
    parser.add_argument('--force-download', action='store_true',
                       help='Force re-download of Pink Sheet data even if cached')
    parser.add_argument('--skip-charts', action='store_true',
                       help='Skip visualization generation (useful for automated pipelines)')
    
    args = parser.parse_args()
    
    try:
        logger.info("="*60)
        logger.info("RICE PRICE SPREAD ANALYSIS PIPELINE")
        logger.info("="*60)
        logger.info(f"Configuration:")
        logger.info(f"  - Start Year: {args.start_year}")
        logger.info(f"  - Force Download: {args.force_download}")
        logger.info(f"  - Generate Charts: {not args.skip_charts}")
        logger.info(f"  - Output Directory: {PROCESSED_DATA_DIR}")
        
        # Execute pipeline stages
        logger.info("\n[Stage 1/7] Downloading World Bank Pink Sheet data...")
        excel_path = download_pink_sheet_data(force_download=args.force_download)
        
        logger.info("\n[Stage 2/7] Extracting rice price time series...")
        rice_prices_df = extract_rice_price_data(excel_path, start_year=args.start_year)
        
        logger.info("\n[Stage 3/7] Computing price spreads...")
        spreads_df, spreads_pct_df = compute_price_spreads(rice_prices_df)
        
        logger.info("\n[Stage 4/7] Preparing data for BigQuery...")
        bq_ready_df = prepare_for_bigquery(spreads_df)
        
        logger.info("\n[Stage 5/7] Saving processed data files...")
        saved_files = save_processed_data(spreads_df, spreads_pct_df, bq_ready_df)
        
        if not args.skip_charts:
            logger.info("\n[Stage 6/7] Creating visualization charts...")
            chart_files = create_visualizations(spreads_df, spreads_pct_df)
            saved_files.update(chart_files)
        else:
            logger.info("\n[Stage 6/7] Skipping chart generation (--skip-charts flag)")
        
        logger.info("\n[Stage 7/7] Generating summary statistics...")
        summary = generate_summary_statistics(spreads_df, spreads_pct_df)
        
        # Final summary report
        logger.info("\n" + "="*60)
        logger.info("PIPELINE EXECUTION COMPLETE")
        logger.info("="*60)
        logger.info(f"Processed {len(rice_prices_df)} months of rice price data")
        logger.info(f"Date range: {rice_prices_df['Date'].min()} to {rice_prices_df['Date'].max()}")
        
        logger.info("\nGenerated outputs:")
        for file_type, file_path in saved_files.items():
            logger.info(f"  ✓ {file_type}: {file_path.name}")
        
        logger.info("\nBigQuery Integration Ready:")
        logger.info("  ✓ CSV file for batch loading via 'bq load' command")
        logger.info("  ✓ JSON Lines file for streaming via Pub/Sub")
        logger.info("  ✓ Metadata and partitioning columns included")
        logger.info("  ✓ Unique record IDs for idempotent loading")
        
        logger.info("\nNext steps for Milestone 2.6 (Data Pipeline):")
        logger.info("  1. Set up Pub/Sub topic for rice price data")
        logger.info("  2. Configure Cloud Dataflow job to stream JSON Lines to BigQuery")
        logger.info("  3. Create BigQuery dataset and table with appropriate schema")
        logger.info("  4. Set up scheduled Cloud Function to run this pipeline daily")
        
        return saved_files
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        logger.error("Please check the logs above for details")
        raise

if __name__ == "__main__":
    main()
