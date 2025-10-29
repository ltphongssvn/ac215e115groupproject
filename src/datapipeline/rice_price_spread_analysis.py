#!/usr/bin/env python3
# File path: ~/code/ltphongssvn/ac215e115groupproject/data-pipeline/rice_price_spread_analysis_fixed.py

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend to save files instead of showing
import matplotlib.pyplot as plt
import requests
import logging
import json
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PINKSHEET_XLSX_URL = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw" / "external_rice_market" / "worldbank_pink_sheet"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Updated mapping to match actual column names with spaces and spelling
RICE_SERIES_MAPPING = {
    "Thai 5%": "Rice, Thai 5%",      # Note: has trailing space in Excel
    "Thai 25%": "Rice, Thai 25%",    # Note: has trailing space in Excel
    "Thai A.1": "Rice, Thai A.1",
    "Vietnamese 5%": "Rice, Viet Namese 5%"  # Different spelling in data
}

def download_pink_sheet_data(force_download=False):
    today_str = datetime.now().strftime("%Y%m%d")
    excel_filename = f"CMO-Historical-Data-Monthly_{today_str}.xlsx"
    excel_path = RAW_DATA_DIR / excel_filename

    if excel_path.exists() and not force_download:
        logger.info(f"Using cached: {excel_path}")
        return excel_path

    logger.info("Downloading World Bank Pink Sheet...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(PINKSHEET_XLSX_URL, headers=headers, timeout=30)
    response.raise_for_status()

    with open(excel_path, 'wb') as f:
        f.write(response.content)

    logger.info(f"Downloaded to: {excel_path}")
    return excel_path

def extract_rice_price_data(excel_path, start_year=2008):
    logger.info(f"Extracting rice prices from {start_year}...")

    # Read with header=4 to get column names, skiprows=5 to skip units row
    df_header = pd.read_excel(excel_path, sheet_name='Monthly Prices', header=4, nrows=0)

    # Read actual data skipping header and units rows
    df = pd.read_excel(excel_path, sheet_name='Monthly Prices', skiprows=6)

    # Use column names from header row
    df.columns = df_header.columns

    # First column contains dates like '1960M01'
    df.rename(columns={df.columns[0]: 'Date'}, inplace=True)

    # Convert date format from '1960M01' to datetime
    df['Date'] = pd.to_datetime(df['Date'].astype(str).str.replace('M', '-'), format='%Y-%m', errors='coerce')

    # Remove rows with invalid dates
    df = df[df['Date'].notna()]

    # Filter by start year
    df = df[df['Date'] >= f'{start_year}-01-01']

    # Find rice columns - handle trailing spaces
    rice_columns_found = {}
    for label, col_pattern in RICE_SERIES_MAPPING.items():
        for col in df.columns:
            # Strip spaces for comparison
            if col_pattern.strip() in str(col).strip():
                rice_columns_found[label] = col
                break

    if not rice_columns_found:
        # Try more flexible matching
        for label, col_pattern in RICE_SERIES_MAPPING.items():
            for col in df.columns:
                # Case-insensitive partial match
                if 'rice' in str(col).lower() and (
                        ('thai 5' in str(col).lower() and label == "Thai 5%") or
                        ('thai 25' in str(col).lower() and label == "Thai 25%") or
                        ('thai a' in str(col).lower() and label == "Thai A.1") or
                        ('viet' in str(col).lower() and '5' in str(col) and label == "Vietnamese 5%")
                ):
                    rice_columns_found[label] = col
                    break

    if not rice_columns_found:
        logger.error(f"No rice columns found. Available: {list(df.columns[:30])}")
        raise ValueError("Rice price columns not found")

    logger.info(f"Found rice columns: {rice_columns_found}")

    # Select date and rice columns
    columns_to_keep = ['Date'] + list(rice_columns_found.values())
    df = df[columns_to_keep]

    # Rename columns to standardized names
    rename_dict = {v: k for k, v in rice_columns_found.items()}
    df = df.rename(columns=rename_dict)

    # Convert price columns to numeric
    price_cols = [col for col in df.columns if col != 'Date']
    for col in price_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Remove rows with all NaN prices
    df = df.dropna(subset=price_cols, how='all')
    df = df.sort_values('Date')

    logger.info(f"Extracted {len(df)} months from {df['Date'].min()} to {df['Date'].max()}")
    return df

def compute_price_spreads(df):
    logger.info("Computing price spreads...")
    spreads_df = df[['Date']].copy()
    spreads_pct_df = df[['Date']].copy()

    if 'Thai 5%' not in df.columns:
        raise ValueError("Thai 5% benchmark not found")

    base_price = df['Thai 5%']

    for variety in ['Thai 25%', 'Thai A.1', 'Vietnamese 5%']:
        if variety in df.columns:
            spreads_df[f'{variety}_spread_usd'] = base_price - df[variety]
            spreads_pct_df[f'{variety}_spread_pct'] = (base_price - df[variety]) / base_price * 100

            # Log statistics
            latest_spread = spreads_df[f'{variety}_spread_usd'].iloc[-1] if len(spreads_df) > 0 else np.nan
            avg_spread = spreads_df[f'{variety}_spread_usd'].mean()
            logger.info(f"{variety}: Latest spread=${latest_spread:.2f}/mt, Average=${avg_spread:.2f}/mt")

    # Include original prices
    for col in df.columns:
        if col != 'Date':
            spreads_df[f'{col}_price'] = df[col]
            spreads_pct_df[f'{col}_price'] = df[col]

    return spreads_df, spreads_pct_df

def create_visualizations(spreads_df, spreads_pct_df):
    logger.info("Creating charts...")

    plt.style.use('seaborn-v0_8-darkgrid')

    # Main comprehensive chart
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Rice Market Price Spread Analysis', fontsize=16, fontweight='bold')

    # Plot spreads
    ax1 = axes[0, 0]
    for col in spreads_df.columns:
        if 'spread_usd' in col:
            variety = col.replace('_spread_usd', '')
            ax1.plot(spreads_df['Date'], spreads_df[col], label=variety, linewidth=2)
    ax1.set_title('Rice Grade Spreads vs Thai 5% (USD/mt)')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Spread (USD/mt)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)

    # Plot percentage spreads
    ax2 = axes[0, 1]
    for col in spreads_pct_df.columns:
        if 'spread_pct' in col:
            variety = col.replace('_spread_pct', '')
            ax2.plot(spreads_pct_df['Date'], spreads_pct_df[col], label=variety, linewidth=2)
    ax2.set_title('Relative Price Spreads (%)')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Spread (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)

    # Plot actual prices
    ax3 = axes[1, 0]
    for col in spreads_df.columns:
        if '_price' in col and 'spread' not in col:
            variety = col.replace('_price', '')
            ax3.plot(spreads_df['Date'], spreads_df[col], label=variety, linewidth=2)
    ax3.set_title('Rice Prices by Grade (USD/mt)')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Price (USD/mt)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Box plot for spread distribution
    ax4 = axes[1, 1]
    spread_cols = [col for col in spreads_df.columns if 'spread_usd' in col]
    if spread_cols:
        spread_data = [spreads_df[col].dropna() for col in spread_cols]
        spread_labels = [col.replace('_spread_usd', '') for col in spread_cols]
        bp = ax4.boxplot(spread_data, tick_labels=spread_labels, patch_artist=True)

        # Color the boxes
        colors = ['lightblue', 'lightgreen', 'lightcoral']
        for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

    ax4.set_title('Spread Distribution Statistics')
    ax4.set_ylabel('Spread (USD/mt)')
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)

    plt.tight_layout()

    # Save to file instead of showing
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    chart_path = PROCESSED_DATA_DIR / f"rice_analysis_comprehensive_{timestamp}.png"
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved chart to: {chart_path}")
    return {'main_chart': chart_path}

def save_processed_data(spreads_df, spreads_pct_df):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save spreads data
    spreads_path = PROCESSED_DATA_DIR / f"rice_spreads_200807_{datetime.now().strftime('%Y%m%d')}.csv"
    spreads_df.to_csv(spreads_path, index=False)

    spreads_pct_path = PROCESSED_DATA_DIR / f"rice_spreads_pct_{timestamp}.csv"
    spreads_pct_df.to_csv(spreads_pct_path, index=False)

    logger.info(f"Saved: {spreads_path} and {spreads_pct_path}")
    return {'spreads_csv': spreads_path, 'spreads_pct_csv': spreads_pct_path}

def generate_summary_statistics(spreads_df, spreads_pct_df):
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
        'percentage_spreads': {}
    }

    # Calculate statistics for absolute spreads
    for col in spreads_df.columns:
        if 'spread_usd' in col:
            variety = col.replace('_spread_usd', '')
            spread_series = spreads_df[col].dropna()

            if len(spread_series) > 0:
                summary['absolute_spreads_usd'][variety] = {
                    'mean': float(spread_series.mean()),
                    'median': float(spread_series.median()),
                    'std_deviation': float(spread_series.std()),
                    'min': float(spread_series.min()),
                    'max': float(spread_series.max()),
                    'latest': float(spread_series.iloc[-1])
                }

    # Calculate percentage spread statistics
    for col in spreads_pct_df.columns:
        if 'spread_pct' in col:
            variety = col.replace('_spread_pct', '')
            pct_series = spreads_pct_df[col].dropna()

            if len(pct_series) > 0:
                summary['percentage_spreads'][variety] = {
                    'mean': float(pct_series.mean()),
                    'median': float(pct_series.median()),
                    'std_deviation': float(pct_series.std()),
                    'latest': float(pct_series.iloc[-1])
                }

    summary_path = PROCESSED_DATA_DIR / f"rice_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Saved statistics: {summary_path}")
    return summary

def main():
    parser = argparse.ArgumentParser(description='Rice Price Spread Analysis')
    parser.add_argument('--start-year', type=int, default=2008)
    parser.add_argument('--force-download', action='store_true')
    parser.add_argument('--skip-charts', action='store_true')
    args = parser.parse_args()

    try:
        logger.info("="*60)
        logger.info("RICE PRICE SPREAD ANALYSIS PIPELINE")
        logger.info("="*60)

        excel_path = download_pink_sheet_data(args.force_download)
        rice_prices_df = extract_rice_price_data(excel_path, args.start_year)
        spreads_df, spreads_pct_df = compute_price_spreads(rice_prices_df)
        saved_files = save_processed_data(spreads_df, spreads_pct_df)

        if not args.skip_charts:
            charts = create_visualizations(spreads_df, spreads_pct_df)
            saved_files.update(charts)

        summary = generate_summary_statistics(spreads_df, spreads_pct_df)

        logger.info("="*60)
        logger.info("PIPELINE COMPLETE")
        logger.info("="*60)
        logger.info(f"Processed {len(rice_prices_df)} months of rice price data")
        logger.info(f"Date range: {rice_prices_df['Date'].min()} to {rice_prices_df['Date'].max()}")
        logger.info("Generated outputs:")
        for file_type, file_path in saved_files.items():
            logger.info(f"  ✓ {file_type}: {file_path.name}")

        return saved_files

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()