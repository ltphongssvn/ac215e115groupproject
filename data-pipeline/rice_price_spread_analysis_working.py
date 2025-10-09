#!/usr/bin/env python3
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/rice_price_spread_analysis_working.py
"""
Working version of Rice Price Spread Analysis Script
Handles trailing spaces in column names and missing data gracefully
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
    Extract rice price data handling trailing spaces and missing data.
    The World Bank data has trailing spaces in some column names and
    uses '...' or '…' to indicate missing data.
    """
    # Find the downloaded file
    excel_files = list(RAW_DATA_DIR.glob("*.xlsx"))
    if not excel_files:
        raise FileNotFoundError("No Excel files found in raw data directory")
    
    excel_path = excel_files[0]
    logger.info(f"Processing file: {excel_path}")
    
    # Read the Excel file with header at row 4
    df = pd.read_excel(excel_path, sheet_name='Monthly Prices', header=4)
    
    # Clean column names - strip whitespace
    df.columns = df.columns.str.strip()
    
    # The first column contains dates
    df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
    
    # Remove the units row if it exists
    first_date_val = str(df.iloc[0]['Date'])
    if 'nan' in first_date_val.lower() or '$' in first_date_val or '(' in first_date_val:
        df = df.iloc[1:]  # Skip the first row with units
    
    # Remove rows where Date is NaN
    df = df[df['Date'].notna()]
    
    # Convert date format from 'YYYYMM' to datetime
    df['Date'] = df['Date'].astype(str)
    df['Date'] = pd.to_datetime(df['Date'].str.replace('M', ''), format='%Y%m', errors='coerce')
    
    # Remove any rows where date conversion failed
    df = df[df['Date'].notna()]
    
    # Filter for dates from start_year onwards
    df = df[df['Date'] >= f'{start_year}-01-01']
    
    # Define the rice columns we want (without trailing spaces now)
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
    
    # Clean up the data - replace '...' and '…' with NaN
    for col in df_rice.columns:
        if col != 'Date':
            # Replace various forms of missing data indicators
            df_rice[col] = df_rice[col].replace(['...', '…', '..', '.'], np.nan)
            # Convert to numeric, coercing errors to NaN
            df_rice[col] = pd.to_numeric(df_rice[col], errors='coerce')
    
    # Clean up column names - remove 'Rice, ' prefix and fix Vietnamese
    rename_dict = {}
    for col in df_rice.columns:
        if col != 'Date':
            clean_name = col.replace('Rice, ', '')
            clean_name = clean_name.replace('Viet Namese', 'Vietnamese')
            rename_dict[col] = clean_name
    
    df_rice.rename(columns=rename_dict, inplace=True)
    
    # Drop rows where all price columns are NaN
    price_cols = [col for col in df_rice.columns if col != 'Date']
    df_rice = df_rice.dropna(subset=price_cols, how='all')
    
    # Sort by date
    df_rice = df_rice.sort_values('Date').reset_index(drop=True)
    
    # Log data availability
    logger.info(f"Extracted {len(df_rice)} rows of data")
    logger.info(f"Date range: {df_rice['Date'].min()} to {df_rice['Date'].max()}")
    logger.info(f"Columns: {list(df_rice.columns)}")
    
    # Check data availability for each variety
    for col in price_cols:
        valid_data = df_rice[col].notna().sum()
        total_rows = len(df_rice)
        logger.info(f"  {col}: {valid_data}/{total_rows} valid prices ({valid_data/total_rows*100:.1f}%)")
    
    return df_rice

def compute_spreads_flexible(df):
    """
    Compute price spreads using available data.
    If Thai 5% is not available, use Thai A.1 as benchmark.
    Handle missing data gracefully.
    """
    spreads_df = df[['Date']].copy()
    
    # Determine which benchmark to use
    if 'Thai 5%' in df.columns and df['Thai 5%'].notna().sum() > 10:
        benchmark = 'Thai 5%'
        base_price = df['Thai 5%']
        logger.info(f"Using {benchmark} as price benchmark")
    elif 'Thai A.1' in df.columns and df['Thai A.1'].notna().sum() > 10:
        benchmark = 'Thai A.1'
        base_price = df['Thai A.1']
        logger.info(f"Thai 5% not available, using {benchmark} as alternative benchmark")
    else:
        logger.error("No suitable benchmark price available")
        return None
    
    # Calculate spreads for other varieties
    for col in df.columns:
        if col != 'Date' and col != benchmark:
            # Only calculate spread if both prices are available
            valid_mask = base_price.notna() & df[col].notna()
            
            if valid_mask.sum() > 0:
                # Absolute spread in USD/mt
                spreads_df[f'{col}_vs_{benchmark}_usd'] = np.nan
                spreads_df.loc[valid_mask, f'{col}_vs_{benchmark}_usd'] = (
                    base_price[valid_mask] - df[col][valid_mask]
                )
                
                # Percentage spread
                spreads_df[f'{col}_vs_{benchmark}_pct'] = np.nan
                spreads_df.loc[valid_mask, f'{col}_vs_{benchmark}_pct'] = (
                    (base_price[valid_mask] - df[col][valid_mask]) / base_price[valid_mask] * 100
                )
                
                valid_count = valid_mask.sum()
                logger.info(f"Calculated spreads for {col}: {valid_count} valid comparisons")
    
    # Add original prices for reference
    for col in df.columns:
        if col != 'Date':
            spreads_df[f'{col}_price'] = df[col]
    
    return spreads_df

def create_adaptive_visualization(spreads_df, output_dir=PROCESSED_DATA_DIR):
    """
    Create visualization that adapts to available data
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Available prices
    ax1 = axes[0, 0]
    price_plotted = False
    for col in spreads_df.columns:
        if '_price' in col:
            variety = col.replace('_price', '')
            # Only plot if there's actual data
            if spreads_df[col].notna().sum() > 0:
                ax1.plot(spreads_df['Date'], spreads_df[col], 
                        label=variety, linewidth=2, marker='o', markersize=2)
                price_plotted = True
    
    if price_plotted:
        ax1.set_title('Rice Prices by Grade (USD/mt)', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Price (USD/mt)')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)
    
    # Plot 2: Absolute spreads
    ax2 = axes[0, 1]
    spread_plotted = False
    for col in spreads_df.columns:
        if '_usd' in col:
            if spreads_df[col].notna().sum() > 0:
                label = col.replace('_usd', '').replace('_vs_', ' vs ')
                ax2.plot(spreads_df['Date'], spreads_df[col], 
                        label=label, linewidth=2, marker='s', markersize=2)
                spread_plotted = True
    
    if spread_plotted:
        ax2.set_title('Price Spreads (USD/mt)', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Spread (USD/mt)')
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Plot 3: Data availability heatmap
    ax3 = axes[1, 0]
    price_cols = [col for col in spreads_df.columns if '_price' in col]
    if price_cols:
        availability_data = []
        variety_names = []
        for col in price_cols:
            variety = col.replace('_price', '')
            variety_names.append(variety)
            # Create monthly availability (1 if data exists, 0 if not)
            monthly_avail = spreads_df.groupby(spreads_df['Date'].dt.to_period('M'))[col].apply(
                lambda x: 1 if x.notna().any() else 0
            ).values
            availability_data.append(monthly_avail)
        
        if availability_data:
            im = ax3.imshow(availability_data, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
            ax3.set_yticks(range(len(variety_names)))
            ax3.set_yticklabels(variety_names)
            ax3.set_xlabel('Month Index')
            ax3.set_title('Data Availability by Variety', fontsize=12, fontweight='bold')
            plt.colorbar(im, ax=ax3, label='Available')
    
    # Plot 4: Summary statistics
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    summary_text = "SUMMARY STATISTICS\n" + "="*30 + "\n\n"
    
    for col in spreads_df.columns:
        if '_price' in col:
            variety = col.replace('_price', '')
            valid_data = spreads_df[col].notna()
            if valid_data.sum() > 0:
                mean_price = spreads_df.loc[valid_data, col].mean()
                last_price = spreads_df.loc[valid_data, col].iloc[-1]
                summary_text += f"{variety}:\n"
                summary_text += f"  Mean: ${mean_price:.2f}/mt\n"
                summary_text += f"  Latest: ${last_price:.2f}/mt\n"
                summary_text += f"  Data points: {valid_data.sum()}\n\n"
    
    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, 
            fontsize=10, verticalalignment='top', fontfamily='monospace')
    
    plt.suptitle('Rice Market Analysis - World Bank Pink Sheet Data', 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    # Save the chart
    chart_path = output_dir / f"rice_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    logger.info(f"Saved visualization to: {chart_path}")
    plt.close()
    
    return chart_path

def main():
    """
    Run the complete analysis pipeline with robust error handling
    """
    try:
        logger.info("="*60)
        logger.info("RICE PRICE SPREAD ANALYSIS - WORKING VERSION")
        logger.info("="*60)
        
        # Extract data
        logger.info("\nStep 1: Extracting rice price data...")
        rice_data = extract_and_process_rice_data(start_year=2022)
        
        if rice_data is None or len(rice_data) == 0:
            logger.error("No data extracted. Please check the input file.")
            return None
        
        # Compute spreads with flexible benchmark
        logger.info("\nStep 2: Computing price spreads...")
        spreads = compute_spreads_flexible(rice_data)
        
        if spreads is None:
            logger.warning("Could not compute spreads due to insufficient data")
            spreads = rice_data  # Just use the price data
        
        # Save results
        logger.info("\nStep 3: Saving results...")
        csv_path = PROCESSED_DATA_DIR / f"rice_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Determine what to save
        if spreads is not None:
            spreads.to_csv(csv_path, index=False)
            data_to_viz = spreads
        else:
            rice_data.to_csv(csv_path, index=False)
            data_to_viz = rice_data
            
        logger.info(f"Saved data to: {csv_path}")
        
        # Create visualization
        logger.info("\nStep 4: Creating adaptive visualization...")
        chart_path = create_adaptive_visualization(data_to_viz)
        
        logger.info("\n" + "="*60)
        logger.info("ANALYSIS COMPLETE!")
        logger.info("="*60)
        logger.info("\nNote: The World Bank Pink Sheet data shows limited availability")
        logger.info("for some rice varieties in recent periods. The analysis has")
        logger.info("adapted to use available data where possible.")
        
        return data_to_viz
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()
