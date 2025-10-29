#!/usr/bin/env python3
# File: src/datapipeline/integrate_all_data_final.py
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
import warnings

# Suppress specific warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directories
PROJECT_ROOT = Path(__file__).parent.parent.parent
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


def load_market_factors_from_source():
    """Load market factors directly from source APIs (fallback if CSV not found)."""
    import requests
    import io

    logger.info("Fetching market factors from source APIs...")

    START = pd.Timestamp("2008-07-01")
    END = pd.Timestamp("2024-12-31")

    def _enforce_monthly(s: pd.Series) -> pd.Series:
        """Ensure monthly start (MS) index and trim NaNs."""
        s = s[~s.index.duplicated(keep="last")].sort_index()
        s = s.resample("MS").mean()
        return s.loc[s.first_valid_index(): s.last_valid_index()]

    def _annual_to_monthly(df_yearly: pd.DataFrame, col: str, name: str) -> pd.Series:
        """Convert annual data to monthly by interpolation."""
        df = df_yearly.dropna(subset=[col]).sort_values("Year")
        idx = pd.to_datetime(df["Year"].astype(str) + "-01-01")
        s = pd.Series(df[col].values, index=idx, name=name)
        s = s.resample("MS").asfreq().interpolate(method="time")
        return s[(s.index >= START) & (s.index <= END)]

    # 1. Oil prices
    try:
        url = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        xls = pd.ExcelFile(io.BytesIO(r.content))
        sheet = next((s for s in ["Monthly Prices","Monthly","Prices","Data"] if s in xls.sheet_names), xls.sheet_names[0])
        df = pd.read_excel(io.BytesIO(r.content), sheet_name=sheet, header=4)
        df.columns = df.columns.map(str).map(str.strip)

        if isinstance(df.iloc[0,0], str) and ("$" in df.iloc[0,0] or "Index" in df.iloc[0,0]):
            df = df.iloc[1:].reset_index(drop=True)

        date_col = df.columns[0]
        raw_date = df[date_col].astype(str).str.strip()
        if raw_date.str.match(r"^\d{4}M\d{2}$").any():
            df["Date"] = pd.to_datetime(raw_date.str.replace("M","", regex=False), format="%Y%m", errors="coerce")
        else:
            df["Date"] = pd.to_datetime(raw_date, errors="coerce")

        candidates = [c for c in df.columns if any(k in c.lower() for k in ["dubai","oman"])]
        oil_col = candidates[0] if candidates else None
        if oil_col:
            df[oil_col] = pd.to_numeric(df[oil_col], errors="coerce")
            oil_series = pd.Series(df[oil_col].values, index=df["Date"], name="Oil_Dubai_Oman_USD_per_bbl")
            oil_series = _enforce_monthly(oil_series[(oil_series.index>=START)&(oil_series.index<=END)])
    except Exception as e:
        logger.warning(f"Could not load oil prices: {e}")
        oil_series = pd.Series(name="Oil_Dubai_Oman_USD_per_bbl")

    # 2-4. Inflation, Population from World Bank API
    series_list = [oil_series]
    countries = ["IN","CN","ID","TH","VN","PH"]

    indicators = {
        "FP.CPI.TOTL.ZG": ("Inflation", "Inflation_Asia_Avg_pct"),
        "SP.POP.GROW": ("Value", "Population_Growth_Asia_Avg_pct"),
        "SP.POP.TOTL": ("Value", "Population_Total_Asia_Avg_millions")
    }

    for ind_code, (value_col, series_name) in indicators.items():
        try:
            url = f"https://api.worldbank.org/v2/country/{';'.join(countries)}/indicator/{ind_code}?date={START.year}:{END.year}&format=json&per_page=20000"
            df = pd.json_normalize(requests.get(url).json()[1])
            df["Year"] = df["date"].astype(int)
            df[value_col] = pd.to_numeric(df["value"], errors="coerce")
            yearly = df.groupby("Year")[value_col].mean().reset_index()
            s = _annual_to_monthly(yearly, value_col, series_name)
            if series_name == "Population_Total_Asia_Avg_millions":
                s = s / 1e6  # Convert to millions
            series_list.append(s)
        except Exception as e:
            logger.warning(f"Could not load {series_name}: {e}")
            series_list.append(pd.Series(name=series_name))

    # 5. ENSO
    try:
        url = "https://psl.noaa.gov/data/correlation/nina34.data"
        df = pd.read_fwf(url, skiprows=1, widths=[5]+[7]*12, header=None)
        df = df.rename(columns={0:"Year",1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"})
        df = df.melt(id_vars=["Year"], var_name="Month", value_name="Anomaly")
        df["Date"] = pd.to_datetime(df["Year"].astype(str)+df["Month"], format="%Y%b", errors="coerce")
        df["Anomaly"] = pd.to_numeric(df["Anomaly"], errors="coerce").replace(-99.99, np.nan)
        enso_series = pd.Series(df["Anomaly"].values, index=df["Date"], name="ENSO_Nino34_Anomaly")
        enso_series = _enforce_monthly(enso_series[(enso_series.index>=START)&(enso_series.index<=END)])
        series_list.append(enso_series)
    except Exception as e:
        logger.warning(f"Could not load ENSO: {e}")
        series_list.append(pd.Series(name="ENSO_Nino34_Anomaly"))

    # 6. Fertilizer
    try:
        url = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"
        df = pd.read_excel(url, sheet_name="Monthly Prices", skiprows=4)
        df = df.rename(columns={df.columns[0]:"Date"})
        df.columns = df.columns.str.strip()
        fert_cols = [c for c in ["DAP","TSP","Urea","Phosphate rock","Potassium chloride **"] if c in df.columns]
        df["Date"] = pd.to_datetime(df["Date"].astype(str), format="%YM%m", errors="coerce")
        for c in fert_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["Composite"] = df[fert_cols].mean(axis=1, skipna=True)
        fert_series = pd.Series(df["Composite"].values, index=df["Date"], name="Fertilizer_Composite_USD_per_mt")
        fert_series = _enforce_monthly(fert_series[(fert_series.index>=START)&(fert_series.index<=END)])
        series_list.append(fert_series)
    except Exception as e:
        logger.warning(f"Could not load fertilizer: {e}")
        series_list.append(pd.Series(name="Fertilizer_Composite_USD_per_mt"))

    # Align all series
    counts = [s.notna().sum() for s in series_list]
    master = series_list[int(np.argmax(counts))].index
    df_market = pd.concat(series_list, axis=1).reindex(master).sort_index()
    df_market = df_market.interpolate(method="time", limit_direction="both")
    df_market = df_market.reset_index().rename(columns={"index": "Date"})

    # Save to CSV for future use
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = PROCESSED_DIR / f"market_factors_{timestamp}.csv"
    df_market.to_csv(output_file, index=False)
    logger.info(f"Saved market factors to {output_file}")

    return df_market


def main():
    """Main integration function combining all data sources."""
    logger.info("="*60)
    logger.info("FINAL COMPREHENSIVE DATA INTEGRATION")
    logger.info("="*60)

    # Step 1: Load rice data
    logger.info("\n[Step 1/4] Loading rice price data...")
    try:
        # Try the pct file first (which contains price columns too)
        df_rice = load_latest_file("rice_spreads_pct_*.csv")
    except FileNotFoundError:
        try:
            # Fallback to non-pct file
            df_rice = load_latest_file("rice_spreads_*.csv")
        except FileNotFoundError:
            logger.error("No rice price data found!")
            raise

    df_rice['Date'] = pd.to_datetime(df_rice['Date'])
    rice_cols = ['Date', 'Thai 5%_price', 'Thai 25%_price', 'Thai A.1_price', 'Vietnamese 5%_price']
    df_rice = df_rice[[col for col in rice_cols if col in df_rice.columns]]
    logger.info(f"Loaded rice data: {len(df_rice)} records")

    # Step 2: Load market factors
    logger.info("\n[Step 2/4] Loading market factors...")
    try:
        df_market = load_latest_file("market_factors_*.csv")
        df_market['Date'] = pd.to_datetime(df_market['Date'])
    except FileNotFoundError:
        logger.info("Market factors CSV not found, fetching from source...")
        df_market = load_market_factors_from_source()
        df_market['Date'] = pd.to_datetime(df_market['Date'])

    logger.info(f"Loaded market factors: {len(df_market)} records")

    # Step 3: Load rainfall data
    logger.info("\n[Step 3/4] Loading rainfall data...")
    try:
        df_rainfall = load_latest_file("rainfall_asia_*.csv")
        df_rainfall['Date'] = pd.to_datetime(df_rainfall['Date'])
        logger.info(f"Loaded rainfall data: {len(df_rainfall)} records")

        # Keep only essential rainfall columns
        rainfall_cols_to_keep = ['Date', 'Asia_Avg_Rainfall_mm', 'Rainfall_Anomaly_pct']
        df_rainfall_subset = df_rainfall[[col for col in rainfall_cols_to_keep if col in df_rainfall.columns]]
    except FileNotFoundError:
        logger.warning("Rainfall data not found, continuing without it...")
        df_rainfall_subset = pd.DataFrame({'Date': df_rice['Date']})

    # Step 4: Merge all datasets
    logger.info("\n[Step 4/4] Merging all datasets...")

    # Merge rice and market factors
    df_integrated = pd.merge(df_rice, df_market, on='Date', how='outer')

    # Merge with rainfall
    df_final = pd.merge(df_integrated, df_rainfall_subset, on='Date', how='outer')
    df_final = df_final.sort_values('Date').reset_index(drop=True)

    # Calculate comprehensive correlations
    logger.info("\nCalculating comprehensive correlations...")

    rice_cols = [col for col in df_final.columns if any(x in col for x in ['Thai 5%', 'Thai 25%', 'Thai A.1', 'Vietnamese'])]

    market_factors = [col for col in df_final.columns if col not in ['Date'] + rice_cols]

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
                'start': str(df_final['Date'].min()),
                'end': str(df_final['Date'].max())
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

    # Show correlation highlights
    if correlations:
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
    logger.info("  • Rice price data")
    logger.info("  • Market factors")
    logger.info("  • Rainfall data (if available)")
    logger.info("  • Ready for machine learning and advanced analysis")

    return df_final


if __name__ == "__main__":
    main()