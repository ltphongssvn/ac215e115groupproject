#!/usr/bin/env python3
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/rice_price_spread_analysis_final.py
"""
Final Rice Price Spread Analysis Script
Configurable to analyze data from any starting period (e.g., 2008M07)
Handles World Bank Pink Sheet data with all known format variations
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
import json

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

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

def parse_start_date(date_str: str) -> pd.Timestamp:
    """
    Parse start date from various formats.
    Accepts: '2008M07', '2008-07', '2008-07-01', 'July 2008'
    
    The flexibility here helps when running the script with different date formats.
    We convert everything to a pandas Timestamp for consistent handling throughout.
    """
    # Try parsing YYYYMM format first (World Bank format)
    if 'M' in date_str.upper():
        # Handle format like '2008M07'
        year_month = date_str.upper().replace('M', '')
        year = int(year_month[:4])
        month = int(year_month[4:])
        return pd.Timestamp(year=year, month=month, day=1)
    
    # Try standard date parsing for other formats
    try:
        return pd.to_datetime(date_str)
    except:
        # If all else fails, try to extract year and month
        parts = date_str.replace('-', ' ').replace('/', ' ').split()
        if len(parts) >= 2:
            try:
                year = int(parts[0]) if parts[0].isdigit() else int(parts[1])
                month = int(parts[1]) if parts[1].isdigit() else 1
                return pd.Timestamp(year=year, month=month, day=1)
            except:
                pass
    
    raise ValueError(f"Could not parse date: {date_str}")

def extract_and_process_rice_data(start_date: str = "2008M07"):
    """
    Extract rice price data from World Bank Pink Sheet.
    
    The start_date parameter allows flexibility in analysis period.
    Using 2008M07 captures the global food crisis period and subsequent recovery,
    providing rich historical context for price spread analysis.
    """
    # Parse the start date
    try:
        start_timestamp = parse_start_date(start_date)
        logger.info(f"Starting analysis from: {start_timestamp.strftime('%B %Y')}")
    except ValueError as e:
        logger.error(f"Invalid start date format: {start_date}")
        raise
    
    # Find the downloaded file
    excel_files = list(RAW_DATA_DIR.glob("*.xlsx"))
    if not excel_files:
        raise FileNotFoundError("No Excel files found in raw data directory")
    
    excel_path = excel_files[0]
    logger.info(f"Processing file: {excel_path}")
    
    # Read the Excel file with proper header location
    df = pd.read_excel(excel_path, sheet_name='Monthly Prices', header=4)
    
    # Clean column names - strip any whitespace
    df.columns = df.columns.str.strip()
    
    # Rename first column to 'Date'
    df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
    
    # Skip units row if present
    first_date_val = str(df.iloc[0]['Date'])
    if 'nan' in first_date_val.lower() or '$' in first_date_val or '(' in first_date_val:
        df = df.iloc[1:]
    
    # Clean date column
    df = df[df['Date'].notna()]
    
    # Parse dates from YYYYMM format
    df['Date'] = df['Date'].astype(str)
    # Remove any 'M' separator and convert to datetime
    df['Date'] = pd.to_datetime(df['Date'].str.replace('M', ''), format='%Y%m', errors='coerce')
    
    # Remove invalid dates
    df = df[df['Date'].notna()]
    
    # Apply date filter based on start_date
    df = df[df['Date'] >= start_timestamp]
    
    logger.info(f"Date range after filtering: {df['Date'].min()} to {df['Date'].max()}")
    logger.info(f"Total months of data: {len(df)}")
    
    # Define target rice columns
    target_columns = [
        'Rice, Thai 5%',
        'Rice, Thai 25%',
        'Rice, Thai A.1',
        'Rice, Viet Namese 5%'
    ]
    
    # Select available rice columns
    columns_to_keep = ['Date']
    for col in target_columns:
        if col in df.columns:
            columns_to_keep.append(col)
            logger.info(f"Found column: {col}")
        else:
            logger.warning(f"Column not found: {col}")
    
    df_rice = df[columns_to_keep].copy()
    
    # Clean data - replace missing indicators with NaN
    for col in df_rice.columns:
        if col != 'Date':
            # Replace ellipsis and similar markers with NaN
            df_rice[col] = df_rice[col].replace(['...', '…', '..', '.', '-', '--'], np.nan)
            # Convert to numeric
            df_rice[col] = pd.to_numeric(df_rice[col], errors='coerce')
    
    # Rename columns for clarity
    rename_dict = {}
    for col in df_rice.columns:
        if col != 'Date':
            clean_name = col.replace('Rice, ', '')
            clean_name = clean_name.replace('Viet Namese', 'Vietnamese')
            rename_dict[col] = clean_name
    
    df_rice.rename(columns=rename_dict, inplace=True)
    
    # Remove rows where all prices are missing
    price_cols = [col for col in df_rice.columns if col != 'Date']
    df_rice = df_rice.dropna(subset=price_cols, how='all')
    
    # Sort chronologically
    df_rice = df_rice.sort_values('Date').reset_index(drop=True)
    
    # Log data quality statistics
    logger.info(f"\nData Quality Report:")
    logger.info(f"Total rows extracted: {len(df_rice)}")
    logger.info(f"Date coverage: {df_rice['Date'].min().strftime('%B %Y')} to {df_rice['Date'].max().strftime('%B %Y')}")
    
    for col in price_cols:
        valid_data = df_rice[col].notna().sum()
        total_rows = len(df_rice)
        completeness = valid_data/total_rows*100
        logger.info(f"  {col}: {valid_data}/{total_rows} valid prices ({completeness:.1f}% complete)")
        
        # Additional statistics for longer time series
        if valid_data > 0:
            mean_price = df_rice[col].mean()
            std_price = df_rice[col].std()
            cv = (std_price / mean_price * 100) if mean_price > 0 else 0
            logger.info(f"    Mean: ${mean_price:.2f}/mt, Std: ${std_price:.2f}/mt, CV: {cv:.1f}%")
    
    return df_rice

def compute_spreads_with_analysis(df):
    """
    Compute price spreads and additional analytical metrics.
    
    For longer time series, we calculate additional metrics like
    moving averages and volatility to provide deeper insights.
    """
    spreads_df = df[['Date']].copy()
    
    # Determine benchmark
    if 'Thai 5%' in df.columns and df['Thai 5%'].notna().sum() > 10:
        benchmark = 'Thai 5%'
        base_price = df['Thai 5%']
        logger.info(f"Using {benchmark} as price benchmark")
    else:
        logger.error("Thai 5% benchmark not available with sufficient data")
        return None
    
    # Calculate spreads for each variety
    for col in df.columns:
        if col != 'Date' and col != benchmark:
            # Valid data mask
            valid_mask = base_price.notna() & df[col].notna()
            
            if valid_mask.sum() > 0:
                # Absolute spread
                spreads_df[f'{col}_spread_usd'] = np.nan
                spreads_df.loc[valid_mask, f'{col}_spread_usd'] = (
                    base_price[valid_mask] - df[col][valid_mask]
                )
                
                # Percentage spread
                spreads_df[f'{col}_spread_pct'] = np.nan
                spreads_df.loc[valid_mask, f'{col}_spread_pct'] = (
                    (base_price[valid_mask] - df[col][valid_mask]) / base_price[valid_mask] * 100
                )
                
                # For longer time series, add moving averages
                if valid_mask.sum() > 12:  # At least one year of data
                    # 12-month moving average of spreads
                    spreads_df[f'{col}_spread_ma12'] = (
                        spreads_df[f'{col}_spread_usd'].rolling(window=12, min_periods=6).mean()
                    )
                
                valid_count = valid_mask.sum()
                logger.info(f"Calculated spreads for {col}: {valid_count} valid comparisons")
    
    # Add original prices
    for col in df.columns:
        if col != 'Date':
            spreads_df[f'{col}_price'] = df[col]
            
            # Add 12-month moving average for prices too
            if df[col].notna().sum() > 12:
                spreads_df[f'{col}_price_ma12'] = (
                    df[col].rolling(window=12, min_periods=6).mean()
                )
    
    return spreads_df

def create_comprehensive_visualization(spreads_df, output_dir=PROCESSED_DATA_DIR):
    """
    Create detailed visualizations for longer time series analysis.
    
    With data from 2008, we can show different market phases including
    the 2008 food crisis, the 2011-2012 price spike, and recent trends.
    """
    # Create larger figure for comprehensive analysis
    fig = plt.figure(figsize=(16, 12))
    
    # Define grid for subplots
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # Plot 1: Rice prices over time with moving averages
    ax1 = fig.add_subplot(gs[0, :])
    for col in spreads_df.columns:
        if '_price' in col and '_ma12' not in col:
            variety = col.replace('_price', '')
            # Plot actual prices
            if spreads_df[col].notna().sum() > 0:
                ax1.plot(spreads_df['Date'], spreads_df[col], 
                        label=variety, linewidth=1.5, alpha=0.7)
                # Add moving average if available
                ma_col = f'{col}_ma12'
                if ma_col in spreads_df.columns:
                    ax1.plot(spreads_df['Date'], spreads_df[ma_col], 
                            linewidth=2, linestyle='--', alpha=0.8)
    
    ax1.set_title('Rice Prices Over Time (with 12-month Moving Averages)', 
                 fontsize=14, fontweight='bold')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price (USD/mt)')
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Format x-axis for better date display
    ax1.xaxis.set_major_locator(mdates.YearLocator(2))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_minor_locator(mdates.YearLocator())
    
    # Add shaded regions for major market events
    # 2008 food crisis
    ax1.axvspan(pd.Timestamp('2008-01-01'), pd.Timestamp('2008-12-31'), 
               alpha=0.1, color='red', label='2008 Crisis')
    # 2011-2012 price spike
    ax1.axvspan(pd.Timestamp('2011-01-01'), pd.Timestamp('2012-06-01'), 
               alpha=0.1, color='orange')
    
    # Plot 2: Absolute spreads
    ax2 = fig.add_subplot(gs[1, 0])
    for col in spreads_df.columns:
        if '_spread_usd' in col and '_ma' not in col:
            if spreads_df[col].notna().sum() > 0:
                label = col.replace('_spread_usd', '').replace('_vs_Thai 5%', '')
                ax2.plot(spreads_df['Date'], spreads_df[col], 
                        label=label, linewidth=1.5, alpha=0.7)
    
    ax2.set_title('Price Spreads vs Thai 5% (USD/mt)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Spread (USD/mt)')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    # Plot 3: Percentage spreads
    ax3 = fig.add_subplot(gs[1, 1])
    for col in spreads_df.columns:
        if '_spread_pct' in col:
            if spreads_df[col].notna().sum() > 0:
                label = col.replace('_spread_pct', '').replace('_vs_Thai 5%', '')
                ax3.plot(spreads_df['Date'], spreads_df[col], 
                        label=label, linewidth=1.5, alpha=0.7)
    
    ax3.set_title('Relative Price Spreads (%)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Spread (%)')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    # Plot 4: Spread distribution (box plots by year)
    ax4 = fig.add_subplot(gs[2, :])
    
    # Prepare data for box plot by year
    spreads_df['Year'] = spreads_df['Date'].dt.year
    spread_cols = [col for col in spreads_df.columns if '_spread_usd' in col and '_ma' not in col]
    
    if spread_cols:
        # Create box plot data grouped by year
        years = sorted(spreads_df['Year'].unique())
        # Limit to recent years for clarity
        recent_years = years[-10:] if len(years) > 10 else years
        
        box_data = []
        box_labels = []
        for year in recent_years:
            year_data = spreads_df[spreads_df['Year'] == year]
            for col in spread_cols:
                data = year_data[col].dropna()
                if len(data) > 0:
                    box_data.append(data)
                    variety = col.replace('_spread_usd', '').replace('_vs_Thai 5%', '')
                    box_labels.append(f'{variety}\n{year}')
        
        if box_data:
            bp = ax4.boxplot(box_data, labels=box_labels, patch_artist=True)
            # Color boxes by variety
            colors = ['lightblue', 'lightgreen', 'lightcoral'] * len(recent_years)
            for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
        
        ax4.set_title('Distribution of Price Spreads by Year', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Spread (USD/mt)')
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.suptitle(f'Rice Market Analysis - World Bank Pink Sheet Data\n'
                f'Period: {spreads_df["Date"].min().strftime("%B %Y")} to '
                f'{spreads_df["Date"].max().strftime("%B %Y")}',
                fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    
    # Save the chart
    chart_path = output_dir / f"rice_analysis_comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    logger.info(f"Saved comprehensive visualization to: {chart_path}")
    plt.close()
    
    return chart_path

def generate_detailed_statistics(spreads_df, output_dir=PROCESSED_DATA_DIR):
    """
    Generate comprehensive statistics for the longer time series.
    
    With data from 2008, we can calculate period-specific statistics
    to understand how market dynamics have changed over time.
    """
    stats = {
        'metadata': {
            'analysis_date': datetime.now().isoformat(),
            'start_date': spreads_df['Date'].min().isoformat(),
            'end_date': spreads_df['Date'].max().isoformat(),
            'total_months': len(spreads_df),
            'data_source': 'World Bank Pink Sheet'
        },
        'overall_statistics': {},
        'period_analysis': {},
        'correlation_matrix': {}
    }
    
    # Overall statistics for each variety
    price_cols = [col for col in spreads_df.columns if '_price' in col and '_ma' not in col]
    for col in price_cols:
        variety = col.replace('_price', '')
        valid_data = spreads_df[col].dropna()
        if len(valid_data) > 0:
            stats['overall_statistics'][variety] = {
                'mean': float(valid_data.mean()),
                'median': float(valid_data.median()),
                'std': float(valid_data.std()),
                'min': float(valid_data.min()),
                'max': float(valid_data.max()),
                'cv': float(valid_data.std() / valid_data.mean() * 100),
                'valid_months': len(valid_data)
            }
    
    # Period-specific analysis
    periods = [
        ('2008-2009 Crisis', '2008-07-01', '2009-12-31'),
        ('2010-2011 Recovery', '2010-01-01', '2011-12-31'),
        ('2012-2015 Stability', '2012-01-01', '2015-12-31'),
        ('2016-2019 Pre-COVID', '2016-01-01', '2019-12-31'),
        ('2020-2022 COVID Period', '2020-01-01', '2022-12-31'),
        ('2023-Present', '2023-01-01', spreads_df['Date'].max().isoformat())
    ]
    
    for period_name, start, end in periods:
        period_data = spreads_df[(spreads_df['Date'] >= start) & (spreads_df['Date'] <= end)]
        if len(period_data) > 0:
            stats['period_analysis'][period_name] = {}
            for col in price_cols:
                variety = col.replace('_price', '')
                valid_data = period_data[col].dropna()
                if len(valid_data) > 0:
                    stats['period_analysis'][period_name][variety] = {
                        'mean': float(valid_data.mean()),
                        'volatility': float(valid_data.std()),
                        'months': len(valid_data)
                    }
    
    # Correlation analysis
    if len(price_cols) > 1:
        price_data = spreads_df[price_cols].dropna()
        if len(price_data) > 10:
            corr_matrix = price_data.corr()
            stats['correlation_matrix'] = corr_matrix.to_dict()
    
    # Save statistics to JSON
    stats_path = output_dir / f"rice_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Saved detailed statistics to: {stats_path}")
    
    # Log key insights
    logger.info("\n" + "="*60)
    logger.info("KEY INSIGHTS FROM ANALYSIS")
    logger.info("="*60)
    
    # Find periods of highest volatility
    for period_name in stats['period_analysis']:
        logger.info(f"\n{period_name}:")
        for variety in stats['period_analysis'][period_name]:
            period_stats = stats['period_analysis'][period_name][variety]
            logger.info(f"  {variety}: Mean=${period_stats['mean']:.2f}, "
                       f"Volatility=${period_stats['volatility']:.2f}")
    
    return stats

def main():
    """
    Main function with command-line argument support for flexible analysis.
    """
    parser = argparse.ArgumentParser(
        description='Rice Price Spread Analysis - World Bank Pink Sheet Data',
        epilog='Analyze rice price spreads over time using World Bank commodity data.'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default='2008M07',
        help='Start date for analysis (e.g., 2008M07, 2015-01, January 2020)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Custom output directory for results'
    )
    
    args = parser.parse_args()
    
    # Set output directory
    output_dir = Path(args.output_dir) if args.output_dir else PROCESSED_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info("="*60)
        logger.info("RICE PRICE SPREAD ANALYSIS")
        logger.info("="*60)
        logger.info(f"Start date: {args.start_date}")
        logger.info(f"Output directory: {output_dir}")
        
        # Step 1: Extract data
        logger.info("\n[Step 1/5] Extracting rice price data...")
        rice_data = extract_and_process_rice_data(start_date=args.start_date)
        
        if rice_data is None or len(rice_data) == 0:
            logger.error("No data extracted. Check input file and date range.")
            return None
        
        # Step 2: Compute spreads
        logger.info("\n[Step 2/5] Computing price spreads...")
        spreads = compute_spreads_with_analysis(rice_data)
        
        if spreads is None:
            logger.warning("Could not compute spreads - using price data only")
            spreads = rice_data
        
        # Step 3: Save data
        logger.info("\n[Step 3/5] Saving processed data...")
        csv_path = output_dir / f"rice_spreads_{args.start_date.replace('M', '')}_{datetime.now().strftime('%Y%m%d')}.csv"
        spreads.to_csv(csv_path, index=False)
        logger.info(f"Saved data to: {csv_path}")
        
        # Step 4: Create visualizations
        logger.info("\n[Step 4/5] Creating comprehensive visualizations...")
        chart_path = create_comprehensive_visualization(spreads, output_dir)
        
        # Step 5: Generate statistics
        logger.info("\n[Step 5/5] Generating detailed statistics...")
        stats = generate_detailed_statistics(spreads, output_dir)
        
        logger.info("\n" + "="*60)
        logger.info("ANALYSIS COMPLETE")
        logger.info("="*60)
        logger.info(f"Analyzed {len(spreads)} months of data")
        logger.info(f"Period: {spreads['Date'].min().strftime('%B %Y')} to "
                   f"{spreads['Date'].max().strftime('%B %Y')}")
        logger.info(f"Results saved in: {output_dir}")
        
        return spreads
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()
