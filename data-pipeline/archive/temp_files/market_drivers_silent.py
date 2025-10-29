#!/usr/bin/env python3
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/market_drivers_silent.py
"""
Modified market_drivers.py that saves plots to files instead of displaying them
All plots are saved to data/processed folder
"""

# Set matplotlib to non-interactive backend before importing pyplot
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import io, re, requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# Output directory for plots
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2008-07-01")
END   = pd.Timestamp("2024-12-31")

PINK_URL = (
    "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021"
    "/related/CMO-Historical-Data-Monthly.xlsx"
)

def download_excel(url: str) -> bytes:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.content

def find_date_column(df: pd.DataFrame) -> str:
    for name in ["Period", "Date", "Month", "TIME", "Time"]:
        if name in df.columns:
            return name
    c0 = df.columns[0]
    ser = df[c0].astype(str).str.strip()
    if ser.str.match(r"^\d{4}M\d{2}$").any():
        return c0
    return c0

def parse_date_column(df: pd.DataFrame, date_col: str) -> pd.Series:
    s = df[date_col].astype(str).str.strip()
    mask = s.str.match(r"^\d{4}M\d{2}$")
    if mask.any():
        return pd.to_datetime(s.str.replace("M","", regex=False), format="%Y%m", errors="coerce")
    return pd.to_datetime(s, errors="coerce")

def pick_dubai_oman_column(df: pd.DataFrame) -> str | None:
    preferred = [
        "Crude oil, Dubai",
        "Crude oil, Dubai/Oman",
        "Crude oil, Oman",
        "Dubai/Oman",
        "Dubai"
    ]
    lowcols = {str(c).strip().lower(): c for c in df.columns}
    for name in preferred:
        key = name.lower()
        if key in lowcols:
            return lowcols[key]
    for c in df.columns:
        cl = str(c).lower()
        if "dubai" in cl or "oman" in cl:
            return c
    return None

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

def load_dubai_oman_oil() -> pd.Series:
    """Load Dubai/Oman oil prices."""
    raw = download_excel(PINK_URL)
    xls = pd.ExcelFile(io.BytesIO(raw))
    
    sheet_candidates = ["Monthly Prices", "Monthly", "Prices", "Data"]
    sheet = None
    for s in sheet_candidates:
        if s in xls.sheet_names:
            sheet = s
            break
    if sheet is None:
        sheet = xls.sheet_names[0]
    
    df = pd.read_excel(io.BytesIO(raw), sheet_name=sheet, header=4)
    df.columns = df.columns.map(lambda x: str(x).strip())
    
    if len(df) and (isinstance(df.iloc[0,0], str) and (("$" in df.iloc[0,0]) or ("Index" in df.iloc[0,0]))):
        df = df.iloc[1:].reset_index(drop=True)
    
    date_col = find_date_column(df)
    df["Date"] = parse_date_column(df, date_col)
    df = df.dropna(subset=["Date"])
    
    price_col = pick_dubai_oman_column(df)
    if price_col is None:
        raise RuntimeError(f"Could not locate Dubai/Oman oil series")
    
    out = df[["Date", price_col]].copy()
    out.rename(columns={price_col: "Oil_Dubai_Oman_USD_per_bbl"}, inplace=True)
    out["Oil_Dubai_Oman_USD_per_bbl"] = (
        out["Oil_Dubai_Oman_USD_per_bbl"]
        .replace(['...', '…', '..', '.', '-', '--'], np.nan)
        .pipe(pd.to_numeric, errors="coerce")
    )
    
    out = out[(out["Date"] >= START) & (out["Date"] <= END)].sort_values("Date").reset_index(drop=True)
    
    print("Series column chosen:", price_col)
    print("Rows:", len(out), "| Date range:", out["Date"].min(), "→", out["Date"].max())
    
    # Save oil price plot
    plt.figure(figsize=(11,4))
    plt.plot(out["Date"], out["Oil_Dubai_Oman_USD_per_bbl"])
    plt.title("Dubai/Oman Benchmark Oil Price (USD/bbl)")
    plt.xlabel("Date")
    plt.ylabel("USD per barrel")
    plt.tight_layout()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plt.savefig(OUTPUT_DIR / f"oil_prices_{timestamp}.png", dpi=100, bbox_inches='tight')
    plt.close()
    print(f"Saved oil price plot to: {OUTPUT_DIR}/oil_prices_{timestamp}.png")
    
    s = pd.Series(out["Oil_Dubai_Oman_USD_per_bbl"].values, 
                  index=out["Date"], name="Oil_Dubai_Oman_USD_per_bbl")
    return _enforce_monthly(s[(s.index>=START)&(s.index<=END)])

def fetch_indicator(countries, indicator, start_year=2008, end_year=2024):
    """Fetch World Bank WDI indicator."""
    country_list = ";".join(countries)
    url = (
        f"https://api.worldbank.org/v2/country/{country_list}/indicator/{indicator}"
        f"?date={start_year}:{end_year}&format=json&per_page=20000"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    records = data[1]
    
    df = pd.json_normalize(records)
    df = df[["country.value", "countryiso3code", "date", "value"]].rename(
        columns={
            "country.value": "Country",
            "countryiso3code": "Code",
            "date": "Year",
            "value": "Value"
        }
    )
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype(int)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df.dropna(subset=["Value"])
    return df

def load_inflation_avg(countries=["IN","CN","ID","TH","VN","PH"]) -> pd.Series:
    """Load inflation data and save plot."""
    IND = "FP.CPI.TOTL.ZG"
    df = fetch_indicator(countries, IND, START.year, END.year)
    
    # Create pivot table for plotting
    df_pivot = df.pivot(index="Year", columns="Country", values="Value").sort_index()
    yearly = df.groupby("Year")["Value"].mean().reset_index()
    
    # Plot inflation
    ax = df_pivot.plot(figsize=(12, 6), marker="o", alpha=0.7)
    yearly_avg = df.groupby("Year")["Value"].mean()
    yearly_avg.plot(ax=ax, color="black", linewidth=2.5, marker="s",
                    label="Yearly Avg (All Countries)")
    plt.title("Consumer Price Inflation (annual %) – Asian Countries & Yearly Average")
    plt.xlabel("Year")
    plt.ylabel("Inflation (%)")
    plt.grid(True, alpha=0.3)
    plt.legend(title="Country / Avg")
    plt.tight_layout()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plt.savefig(OUTPUT_DIR / f"inflation_{timestamp}.png", dpi=100, bbox_inches='tight')
    plt.close()
    print(f"Saved inflation plot to: {OUTPUT_DIR}/inflation_{timestamp}.png")
    
    return _annual_to_monthly(yearly, "Value", "Inflation_Asia_Avg")

def load_population_growth(countries=["IN","CN","ID","TH","VN","PH"]) -> pd.Series:
    """Load population growth data and save plot."""
    IND = "SP.POP.GROW"
    df = fetch_indicator(countries, IND, START.year, END.year)
    
    df_pivot = df.pivot(index="Year", columns="Country", values="Value").sort_index()
    yearly = df.groupby("Year")["Value"].mean().reset_index()
    
    # Plot population growth
    ax = df_pivot.plot(figsize=(12, 6), marker="o", alpha=0.7)
    yearly_avg = df.groupby("Year")["Value"].mean()
    yearly_avg.plot(ax=ax, color="black", linewidth=2.5, marker="s",
                    label="Yearly Avg (All Countries)")
    plt.title("Population Growth (annual %) – Asian Countries & Yearly Average")
    plt.xlabel("Year")
    plt.ylabel("Growth Rate (%)")
    plt.grid(True, alpha=0.3)
    plt.legend(title="Country / Avg")
    plt.tight_layout()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plt.savefig(OUTPUT_DIR / f"population_growth_{timestamp}.png", dpi=100, bbox_inches='tight')
    plt.close()
    print(f"Saved population growth plot to: {OUTPUT_DIR}/population_growth_{timestamp}.png")
    
    return _annual_to_monthly(yearly, "Value", "Population_Growth_Asia_Avg")

def load_population_total(countries=["IN","CN","ID","TH","VN","PH"]) -> pd.Series:
    """Load population total data and save plot."""
    IND = "SP.POP.TOTL"
    df = fetch_indicator(countries, IND, START.year, END.year)
    
    df_pivot = df.pivot(index="Year", columns="Country", values="Value").sort_index()
    yearly = df.groupby("Year")["Value"].mean().reset_index()
    
    # Plot population total
    ax = df_pivot.plot(figsize=(12, 6), marker="o", alpha=0.7)
    yearly_avg = df.groupby("Year")["Value"].mean()
    yearly_avg.plot(ax=ax, color="black", linewidth=2.5, marker="s",
                    label="Yearly Avg (All Countries)")
    plt.title("Total Population – Asian Countries & Yearly Average")
    plt.xlabel("Year")
    plt.ylabel("Population (people)")
    plt.grid(True, alpha=0.3)
    plt.legend(title="Country / Avg")
    plt.tight_layout()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plt.savefig(OUTPUT_DIR / f"population_total_{timestamp}.png", dpi=100, bbox_inches='tight')
    plt.close()
    print(f"Saved population total plot to: {OUTPUT_DIR}/population_total_{timestamp}.png")
    
    return _annual_to_monthly(yearly, "Value", "Population_Total_Asia_Avg")

def load_nino34() -> pd.Series:
    """Load ENSO data and save plot."""
    url = "https://psl.noaa.gov/data/correlation/nina34.data"
    df = pd.read_fwf(url, skiprows=1, widths=[5]+[7]*12, header=None)
    df = df.rename(columns={0:"Year",1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                            7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"})
    df = df.melt(id_vars=["Year"], var_name="Month", value_name="Anomaly")
    df["Date"] = pd.to_datetime(df["Year"].astype(str)+df["Month"], format="%Y%b", errors="coerce")
    df["Anomaly"] = pd.to_numeric(df["Anomaly"], errors="coerce").replace(-99.99, np.nan)
    df = df.dropna(subset=["Date", "Anomaly"]).sort_values("Date").reset_index(drop=True)
    df = df[(df["Date"].dt.year >= START.year) & (df["Date"].dt.year <= END.year)]
    
    # Plot ENSO
    plt.figure(figsize=(14,6))
    plt.plot(df["Date"].values, df["Anomaly"].values, label="Niño 3.4 SST Anomaly", color="tab:blue")
    plt.axhline(0, color="black", linestyle="--")
    plt.axhline(0.5, color="red", linestyle="--", alpha=0.6, label="El Niño threshold (+0.5°C)")
    plt.axhline(-0.5, color="green", linestyle="--", alpha=0.6, label="La Niña threshold (−0.5°C)")
    plt.title("Niño 3.4 Index (ENSO) [2008–2024]")
    plt.xlabel("Date")
    plt.ylabel("SST Anomaly (°C)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plt.savefig(OUTPUT_DIR / f"enso_{timestamp}.png", dpi=100, bbox_inches='tight')
    plt.close()
    print(f"Saved ENSO plot to: {OUTPUT_DIR}/enso_{timestamp}.png")
    
    s = pd.Series(df["Anomaly"].values, index=df["Date"], name="Nino3.4_SST_Anomaly")
    return _enforce_monthly(s[(s.index>=START)&(s.index<=END)])

def load_fertilizer() -> pd.Series:
    """Load fertilizer data and save plot."""
    url = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"
    df = pd.read_excel(url, sheet_name="Monthly Prices", skiprows=4)
    df = df.rename(columns={df.columns[0]:"Date"})
    df.columns = df.columns.str.strip()
    fert_cols = [c for c in ["DAP","TSP","Urea","Phosphate rock","Potassium chloride **"] if c in df.columns]
    df["Date"] = pd.to_datetime(df["Date"].astype(str), format="%YM%m", errors="coerce")
    for c in fert_cols: 
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[(df["Date"].dt.year >= START.year) & (df["Date"].dt.year <= END.year)]
    df["Composite"] = df[fert_cols].mean(axis=1, skipna=True)
    
    # Plot fertilizer prices
    df.set_index("Date")[fert_cols].plot(figsize=(12,6))
    plt.title("Fertilizer Prices (US$/mt) [2008–2024]")
    plt.ylabel("US$/metric ton")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plt.savefig(OUTPUT_DIR / f"fertilizer_{timestamp}.png", dpi=100, bbox_inches='tight')
    plt.close()
    print(f"Saved fertilizer plot to: {OUTPUT_DIR}/fertilizer_{timestamp}.png")
    
    s = pd.Series(df["Composite"].values, index=df["Date"], name="Fertilizer_Composite")
    return _enforce_monthly(s[(s.index>=START)&(s.index<=END)])

def main():
    """Main function to load all data and save plots."""
    print("="*60)
    print("LOADING MARKET DRIVERS AND SAVING PLOTS")
    print("="*60)
    
    loaders = [
        ("Oil", load_dubai_oman_oil),
        ("Inflation", load_inflation_avg),
        ("Population Growth", load_population_growth),
        ("Population Total", load_population_total),
        ("ENSO", load_nino34),
        ("Fertilizer", load_fertilizer)
    ]
    
    series_list = []
    for name, fn in loaders:
        try:
            print(f"\nLoading {name}...")
            s = fn()
            series_list.append(s)
            print(f"✓ Loaded {s.name} ({len(s)} pts)")
        except Exception as e:
            print(f"✗ Error loading {name}: {e}")
    
    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"Successfully loaded {len(series_list)} market factors")
    print(f"All plots saved to: {OUTPUT_DIR}")
    
    return series_list

if __name__ == "__main__":
    main()
