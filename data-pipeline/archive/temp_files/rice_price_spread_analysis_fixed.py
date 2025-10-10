#!/usr/bin/env python3
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/rice_price_spread_analysis_fixed.py
"""
Fixed version of Rice Price Spread Analysis Script
Properly extracts all four rice varieties from World Bank Pink Sheet
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw" / "external_rice_market" / "worldbank_pink_sheet"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Ensure processed directory exists
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

def extract_and_process_rice_data(start_year: int = 2022):
    """
    Extract rice price data with proper column selection.
    The issue was that we need to specifically look for the columns
    by their exact names including the 'Rice, ' prefix.
    """
    # Find the downloaded file
    excel_files = list(RAW_DATA_DIR.glob("*.xlsx"))
    if not excel_files:
        raise FileNotFoundError("No Excel files found in raw data directory")
    
    excel_path = excel_files[0]
    logger.info(f"Processing file: {excel_path}")
    
    # Read the Excel file with header at row 4
    # We don't skip row 5 because it gets handled automatically
    df = pd.read_excel(excel_path, sheet_name='Monthly Prices', header=4)
    
    # The first column contains dates
    df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
    
    # Remove the units row if it exists (first row after header)
    # Check if the first row has non-date values that look like units
    first_date_val = str(df.iloc[0]['Date'])
    if 'nan' in first_date_val.lower() or '$' in first_date_val or '(' in first_date_val:
        df = df.iloc[1:]  # Skip the first row
    
    # Remove rows where Date is NaN
    df = df[df['Date'].notna()]
    
    # Convert date format from 'YYYYMM' to datetime
    # Handle the format where dates are like '1960M01'
    df['Date'] = df['Date'].astype(str)
    df['Date'] = pd.to_datetime(df['Date'].str.replace('M', ''), format='%Y%m', errors='coerce')
    
    # Remove any rows where date conversion failed
    df = df[df['Date'].notna()]
    
    # Filter for dates from start_year onwards
    df = df[df['Date'] >= f'{start_year}-01-01']
    
    # Define the exact column names we're looking for
    target_columns = [
        'Rice, Thai 5%',
        'Rice, Thai 25%',
        'Rice, Thai A.1',
        'Rice, Viet Namese 5%'
    ]
    
    # Select Date plus all rice columns that exist
    columns_to_keep = ['Date']
    for col in target_columns:
        if col in df.columns:
            columns_to_keep.append(col)
            logger.info(f"Found column: {col}")
        else:
            logger.warning(f"Column not found: {col}")
    
    df_rice = df[columns_to_keep].copy()
    
    # Clean up column names - remove 'Rice, ' prefix and fix Vietnamese
    rename_dict = {}
    for col in df_rice.columns:
        if col != 'Date':
            # Remove 'Rice, ' prefix
            clean_name = col.replace('Rice, ', '')
            # Fix Vietnamese spelling
            clean_name = clean_name.replace('Viet Namese', 'Vietnamese')
            rename_dict[col] = clean_name
    
    df_rice.rename(columns=rename_dict, inplace=True)
    
    # Drop rows where all price columns are NaN
    price_cols = [col for col in df_rice.columns if col != 'Date']
    df_rice = df_rice.dropna(subset=price_cols, how='all')
    
    # Sort by date
    df_rice = df_rice.sort_values('Date').reset_index(drop=True)
    
    logger.info(f"Extracted {len(df_rice)} rows of data")
    logger.info(f"Date range: {df_rice['Date'].min()} to {df_rice['Date'].max()}")
    logger.info(f"Columns: {list(df_rice.columns)}")
    
    return df_rice

def compute_spreads(df):
    """
    Compute price spreads using Thai 5% as benchmark
    """
    spreads_df = df[['Date']].copy()
    
    if 'Thai 5%' not in df.columns:
        logger.error(f"Available columns: {df.columns.tolist()}")
        raise ValueError("Thai 5% benchmark not found")
    
    base_price = df['Thai 5%']
    
    # Calculate spreads for other varieties
    varieties = ['Thai 25%', 'Thai A.1', 'Vietnamese 5%']
    
    for variety in varieties:
        if variety in df.columns:
            # Absolute spread in USD/mt
            spreads_df[f'{variety}_spread_usd'] = base_price - df[variety]
            # Percentage spread
            spreads_df[f'{variety}_spread_pct'] = ((base_price - df[variety]) / base_price * 100)
            logger.info(f"Calculated spreads for {variety}")
    
    # Add original prices for reference
    for col in df.columns:
        if col != 'Date':
            spreads_df[f'{col}_price'] = df[col]
    
    return spreads_df

def create_simple_visualization(spreads_df, output_dir=PROCESSED_DATA_DIR):
    """
    Create a simple visualization of the spreads
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot absolute spreads
    for col in spreads_df.columns:
        if '_spread_usd' in col:
            variety = col.replace('_spread_usd', '')
            ax1.plot(spreads_df['Date'], spreads_df[col], label=variety, linewidth=2)
    
    ax1.set_title('Rice Price Spreads vs Thai 5% (USD/mt)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Spread (USD/mt)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Plot actual prices
    for col in spreads_df.columns:
        if '_price' in col:
            variety = col.replace('_price', '')
            ax2.plot(spreads_df['Date'], spreads_df[col], label=variety, linewidth=2)
    
    ax2.set_title('Rice Prices by Grade', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Price (USD/mt)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the chart
    chart_path = output_dir / f"rice_analysis_{datetime.now().strftime('%Y%m%d')}.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    logger.info(f"Saved chart to: {chart_path}")
    plt.close()
    
    return chart_path

def main():
    """
    Run the complete analysis pipeline
    """
    try:
        logger.info("="*60)
        logger.info("RICE PRICE SPREAD ANALYSIS - FIXED VERSION")
        logger.info("="*60)
        
        # Extract data
        logger.info("\nStep 1: Extracting rice price data...")
        rice_data = extract_and_process_rice_data(start_year=2022)
        
        # Compute spreads
        logger.info("\nStep 2: Computing price spreads...")
        spreads = compute_spreads(rice_data)
        
        # Save results
        logger.info("\nStep 3: Saving results...")
        csv_path = PROCESSED_DATA_DIR / f"rice_spreads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        spreads.to_csv(csv_path, index=False)
        logger.info(f"Saved CSV to: {csv_path}")
        
        # Create visualization
        logger.info("\nStep 4: Creating visualization...")
        chart_path = create_simple_visualization(spreads)
        
        # Print summary statistics
        logger.info("\n" + "="*60)
        logger.info("SUMMARY STATISTICS")
        logger.info("="*60)
        
        for col in spreads.columns:
            if '_spread_usd' in col:
                variety = col.replace('_spread_usd', '')
                mean_spread = spreads[col].mean()
                latest_spread = spreads[col].iloc[-1] if len(spreads) > 0 else 0
                std_spread = spreads[col].std()
                
                logger.info(f"\n{variety}:")
                logger.info(f"  Average spread: ${mean_spread:.2f}/mt")
                logger.info(f"  Latest spread: ${latest_spread:.2f}/mt")
                logger.info(f"  Std deviation: ${std_spread:.2f}/mt")
        
        logger.info("\n" + "="*60)
        logger.info("ANALYSIS COMPLETE!")
        logger.info("="*60)
        
        return spreads
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()
