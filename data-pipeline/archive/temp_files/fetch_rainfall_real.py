#!/usr/bin/env python3
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/fetch_rainfall_real.py
"""
Fetch real rainfall data for major rice-producing regions in Asia
Uses multiple data sources:
1. CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data)
2. NOAA PSL (Physical Sciences Laboratory) gridded precipitation data
3. NASA GPM (Global Precipitation Measurement) via OpenDAP
"""

import pandas as pd
import numpy as np
import requests
import xarray as xr
from pathlib import Path
import logging
from datetime import datetime
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class RainfallDataFetcher:
    """
    Fetches precipitation data from multiple sources for Asian rice regions.
    The class design allows for fallback between different data sources.
    """

    def __init__(self):
        # Define major rice-producing regions with their coordinates
        # These coordinates represent agricultural centers in each country
        self.regions = {
            'Thailand': {
                'lat': 15.0, 'lon': 100.0,  # Central Thailand (main rice bowl)
                'box': [97, 105, 5, 20]  # Bounding box [west, east, south, north]
            },
            'Vietnam': {
                'lat': 10.8, 'lon': 106.7,  # Mekong Delta region
                'box': [102, 110, 8, 24]
            },
            'India': {
                'lat': 26.0, 'lon': 80.0,  # Gangetic Plains
                'box': [68, 97, 8, 37]
            },
            'China': {
                'lat': 31.0, 'lon': 120.0,  # Yangtze River Delta
                'box': [73, 135, 18, 54]
            },
            'Indonesia': {
                'lat': -7.0, 'lon': 107.0,  # Java (main rice region)
                'box': [95, 141, -11, 6]
            },
            'Philippines': {
                'lat': 15.5, 'lon': 121.0,  # Central Luzon
                'box': [116, 127, 5, 20]
            }
        }

        # Time range for our analysis
        self.start_date = '2008-07-01'
        self.end_date = '2024-12-01'

    def fetch_chirps_data(self):
        """
        Fetch CHIRPS precipitation data via their data server.
        CHIRPS provides monthly precipitation at 0.05° resolution globally.
        Data available from 1981 to near-present.
        """
        logger.info("Attempting to fetch CHIRPS precipitation data...")

        try:
            # CHIRPS monthly data URL pattern
            # The data is organized by year/month in NetCDF format
            base_url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/netcdf/"

            # Create date range
            dates = pd.date_range(start=self.start_date, end=self.end_date, freq='MS')
            df_rainfall = pd.DataFrame({'Date': dates})

            # For each region, extract precipitation data
            for region_name, region_info in self.regions.items():
                logger.info(f"Fetching CHIRPS data for {region_name}...")

                monthly_precip = []

                # We'll fetch year by year to manage data size
                for year in range(2008, 2025):
                    try:
                        # CHIRPS file naming convention
                        filename = f"chirps-v2.0.{year}.monthly.nc"
                        url = base_url + filename

                        # Open dataset directly from URL using xarray
                        # This uses OpenDAP protocol for efficient data access
                        with xr.open_dataset(url, decode_times=True) as ds:
                            # Extract data for the specific region
                            # Using bounding box for better regional average
                            west, east, south, north = region_info['box']

                            # Select spatial subset
                            ds_region = ds.sel(
                                longitude=slice(west, east),
                                latitude=slice(south, north)
                            )

                            # Calculate spatial average for each month
                            # Weight by latitude to account for grid cell size differences
                            weights = np.cos(np.deg2rad(ds_region.latitude))
                            weights = weights / weights.sum()

                            # Extract precipitation (variable name is 'precip')
                            precip = ds_region['precip']

                            # Calculate weighted mean across space for each time
                            regional_mean = precip.weighted(weights).mean(['latitude', 'longitude'])

                            # Convert to pandas series
                            monthly_values = regional_mean.to_pandas()
                            monthly_precip.extend(monthly_values.values)

                    except Exception as e:
                        logger.warning(f"Could not fetch CHIRPS data for {year}: {e}")
                        # Fill with NaN for missing data
                        months_in_year = 12 if year < 2024 else dates[dates.year == year].shape[0]
                        monthly_precip.extend([np.nan] * months_in_year)

                # Trim to match our date range
                monthly_precip = monthly_precip[:len(dates)]
                df_rainfall[f'{region_name}_rainfall_mm'] = monthly_precip

            # Calculate Asian average (excluding NaN values)
            rainfall_cols = [col for col in df_rainfall.columns if 'rainfall' in col]
            df_rainfall['Asia_Avg_Rainfall_mm'] = df_rainfall[rainfall_cols].mean(axis=1, skipna=True)

            # Calculate anomalies
            long_term_mean = df_rainfall['Asia_Avg_Rainfall_mm'].mean()
            df_rainfall['Rainfall_Anomaly_pct'] = (
                    (df_rainfall['Asia_Avg_Rainfall_mm'] - long_term_mean) / long_term_mean * 100
            )

            logger.info("Successfully fetched CHIRPS data")
            return df_rainfall

        except Exception as e:
            logger.error(f"Failed to fetch CHIRPS data: {e}")
            return None

    def fetch_noaa_cpc_data(self):
        """
        Fetch NOAA CPC (Climate Prediction Center) Unified Gauge-Based precipitation data.
        This provides global land precipitation data at 0.5° resolution.
        """
        logger.info("Attempting to fetch NOAA CPC precipitation data...")

        try:
            # NOAA PSL (Physical Sciences Laboratory) OpenDAP server
            # CPC Unified precipitation dataset
            base_url = "https://psl.noaa.gov/thredds/dodsC/Datasets/cpc_global_precip/"

            dates = pd.date_range(start=self.start_date, end=self.end_date, freq='MS')
            df_rainfall = pd.DataFrame({'Date': dates})

            for region_name, region_info in self.regions.items():
                logger.info(f"Fetching NOAA data for {region_name}...")

                monthly_precip = []

                # NOAA data is organized by variable
                # Monthly data file
                url = base_url + "precip.mon.mean.nc"

                try:
                    # Open dataset via OpenDAP
                    with xr.open_dataset(url, decode_times=True) as ds:
                        # Select time range
                        ds_time = ds.sel(time=slice(self.start_date, self.end_date))

                        # Select spatial region
                        west, east, south, north = region_info['box']

                        # Note: NOAA uses 'lat' and 'lon' instead of 'latitude' and 'longitude'
                        ds_region = ds_time.sel(
                            lon=slice(west, east),
                            lat=slice(south, north)
                        )

                        # Get precipitation data (variable is 'precip')
                        precip = ds_region['precip']

                        # Calculate spatial average
                        # Convert from mm/day to mm/month
                        days_per_month = pd.to_datetime(ds_region.time.values).to_series().dt.days_in_month

                        regional_mean = precip.mean(['lat', 'lon'])
                        monthly_values = regional_mean.values * days_per_month.values

                        monthly_precip = monthly_values.tolist()

                except Exception as e:
                    logger.warning(f"Could not fetch NOAA data for {region_name}: {e}")
                    monthly_precip = [np.nan] * len(dates)

                df_rainfall[f'{region_name}_rainfall_mm'] = monthly_precip[:len(dates)]

            # Calculate Asian average
            rainfall_cols = [col for col in df_rainfall.columns if 'rainfall' in col]
            df_rainfall['Asia_Avg_Rainfall_mm'] = df_rainfall[rainfall_cols].mean(axis=1, skipna=True)

            # Calculate anomalies
            long_term_mean = df_rainfall['Asia_Avg_Rainfall_mm'].mean()
            df_rainfall['Rainfall_Anomaly_pct'] = (
                    (df_rainfall['Asia_Avg_Rainfall_mm'] - long_term_mean) / long_term_mean * 100
            )

            logger.info("Successfully fetched NOAA CPC data")
            return df_rainfall

        except Exception as e:
            logger.error(f"Failed to fetch NOAA data: {e}")
            return None

    def fetch_gpcc_data(self):
        """
        Fetch GPCC (Global Precipitation Climatology Centre) data.
        This is from Germany's DWD and provides high-quality gauge-based precipitation.
        """
        logger.info("Attempting to fetch GPCC precipitation data...")

        try:
            # GPCC data via NOAA PSL
            url = "https://psl.noaa.gov/thredds/dodsC/Datasets/gpcc/full_v2018/precip.mon.total.v2018.nc"

            dates = pd.date_range(start=self.start_date, end=self.end_date, freq='MS')
            df_rainfall = pd.DataFrame({'Date': dates})

            with xr.open_dataset(url, decode_times=True) as ds:
                # Select time range
                ds_time = ds.sel(time=slice(self.start_date, self.end_date))

                for region_name, region_info in self.regions.items():
                    logger.info(f"Processing GPCC data for {region_name}...")

                    # Select spatial region
                    west, east, south, north = region_info['box']

                    ds_region = ds_time.sel(
                        lon=slice(west, east),
                        lat=slice(south, north)
                    )

                    # Calculate regional average
                    precip = ds_region['precip']
                    regional_mean = precip.mean(['lat', 'lon'])

                    df_rainfall[f'{region_name}_rainfall_mm'] = regional_mean.values[:len(dates)]

            # Calculate Asian average
            rainfall_cols = [col for col in df_rainfall.columns if 'rainfall' in col]
            df_rainfall['Asia_Avg_Rainfall_mm'] = df_rainfall[rainfall_cols].mean(axis=1, skipna=True)

            # Calculate anomalies
            long_term_mean = df_rainfall['Asia_Avg_Rainfall_mm'].mean()
            df_rainfall['Rainfall_Anomaly_pct'] = (
                    (df_rainfall['Asia_Avg_Rainfall_mm'] - long_term_mean) / long_term_mean * 100
            )

            logger.info("Successfully fetched GPCC data")
            return df_rainfall

        except Exception as e:
            logger.error(f"Failed to fetch GPCC data: {e}")
            return None

    def fetch_with_fallback(self):
        """
        Try multiple data sources with fallback strategy.
        Priority order: CHIRPS -> NOAA CPC -> GPCC
        """

        # Try CHIRPS first (most reliable for agricultural applications)
        df = self.fetch_chirps_data()
        if df is not None and not df['Asia_Avg_Rainfall_mm'].isna().all():
            logger.info("Using CHIRPS data as primary source")
            return df, "CHIRPS"

        # Fallback to NOAA CPC
        df = self.fetch_noaa_cpc_data()
        if df is not None and not df['Asia_Avg_Rainfall_mm'].isna().all():
            logger.info("Using NOAA CPC data as fallback")
            return df, "NOAA_CPC"

        # Final fallback to GPCC
        df = self.fetch_gpcc_data()
        if df is not None and not df['Asia_Avg_Rainfall_mm'].isna().all():
            logger.info("Using GPCC data as final fallback")
            return df, "GPCC"

        logger.error("All data sources failed")
        return None, None


def main():
    """Main function to fetch and save rainfall data."""
    logger.info("="*60)
    logger.info("FETCHING REAL ASIAN RAINFALL DATA")
    logger.info("="*60)

    # Initialize fetcher
    fetcher = RainfallDataFetcher()

    # Fetch data with fallback strategy
    df_rainfall, source = fetcher.fetch_with_fallback()

    if df_rainfall is None:
        logger.error("Failed to fetch rainfall data from any source")
        logger.info("Please check your internet connection and try again")
        logger.info("Alternative: Install required packages: pip install xarray netcdf4 dask")
        return None

    # Save to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = OUTPUT_DIR / f"rainfall_asia_{timestamp}.csv"
    df_rainfall.to_csv(output_file, index=False)

    # Save metadata
    metadata = {
        'source': source,
        'fetch_date': datetime.now().isoformat(),
        'start_date': fetcher.start_date,
        'end_date': fetcher.end_date,
        'regions': list(fetcher.regions.keys()),
        'data_quality': {
            'missing_values': df_rainfall['Asia_Avg_Rainfall_mm'].isna().sum(),
            'total_months': len(df_rainfall),
            'completeness': f"{(1 - df_rainfall['Asia_Avg_Rainfall_mm'].isna().sum()/len(df_rainfall))*100:.1f}%"
        }
    }

    metadata_file = OUTPUT_DIR / f"rainfall_metadata_{timestamp}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    # Summary statistics
    logger.info("\n" + "="*60)
    logger.info("RAINFALL DATA SUMMARY")
    logger.info("="*60)
    logger.info(f"Data source: {source}")
    logger.info(f"Date range: {df_rainfall['Date'].min()} to {df_rainfall['Date'].max()}")
    logger.info(f"Total months: {len(df_rainfall)}")
    logger.info(f"Data completeness: {metadata['data_quality']['completeness']}")

    # Regional statistics
    logger.info("\nRegional Rainfall Statistics (mm/month):")
    for region in fetcher.regions.keys():
        col = f'{region}_rainfall_mm'
        if col in df_rainfall.columns:
            mean_val = df_rainfall[col].mean()
            std_val = df_rainfall[col].std()
            logger.info(f"  {region:12} - Mean: {mean_val:6.1f}, Std Dev: {std_val:5.1f}")

    # Overall statistics
    logger.info(f"\nAsia Average Statistics:")
    logger.info(f"  Mean: {df_rainfall['Asia_Avg_Rainfall_mm'].mean():.1f} mm/month")
    logger.info(f"  Std Dev: {df_rainfall['Asia_Avg_Rainfall_mm'].std():.1f} mm/month")
    logger.info(f"  Min: {df_rainfall['Asia_Avg_Rainfall_mm'].min():.1f} mm/month")
    logger.info(f"  Max: {df_rainfall['Asia_Avg_Rainfall_mm'].max():.1f} mm/month")

    # Identify extreme events
    extreme_dry = df_rainfall[df_rainfall['Rainfall_Anomaly_pct'] < -30]
    extreme_wet = df_rainfall[df_rainfall['Rainfall_Anomaly_pct'] > 30]

    if len(extreme_dry) > 0:
        logger.info(f"\nDrought Months (< -30% anomaly): {len(extreme_dry)}")
        for _, row in extreme_dry.nlargest(3, 'Rainfall_Anomaly_pct').iterrows():
            logger.info(f"  {row['Date'].strftime('%Y-%m')}: {row['Asia_Avg_Rainfall_mm']:.1f} mm ({row['Rainfall_Anomaly_pct']:.1f}%)")

    if len(extreme_wet) > 0:
        logger.info(f"\nFlood Risk Months (> +30% anomaly): {len(extreme_wet)}")
        for _, row in extreme_wet.nlargest(3, 'Rainfall_Anomaly_pct').iterrows():
            logger.info(f"  {row['Date'].strftime('%Y-%m')}: {row['Asia_Avg_Rainfall_mm']:.1f} mm (+{row['Rainfall_Anomaly_pct']:.1f}%)")

    logger.info(f"\nOutput saved to: {output_file}")
    logger.info(f"Metadata saved to: {metadata_file}")

    return df_rainfall


if __name__ == "__main__":
    # Check required packages
    try:
        import xarray
        import netCDF4
    except ImportError:
        logger.error("Required packages not installed!")
        logger.error("Please run: pip install xarray netcdf4 dask")
        logger.error("These are needed to access climate data servers")
        exit(1)

    main()