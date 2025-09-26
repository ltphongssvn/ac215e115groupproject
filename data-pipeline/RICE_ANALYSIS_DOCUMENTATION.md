# Rice Price Spread Analysis Documentation
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/RICE_ANALYSIS_DOCUMENTATION.md

## Overview

This document provides comprehensive documentation of the rice price spread analysis pipeline, its outputs, and key findings from analyzing World Bank Pink Sheet data from July 2008 to December 2024. This analysis forms a critical component of our ERP AI system's data pipeline (Milestone 2.6) and provides essential input for time-series forecasting models.

## Data Source

The analysis uses the World Bank Commodity Price Data (Pink Sheet), which is updated monthly and provides standardized price data for four key rice varieties:
- Thai 5% (benchmark grade, most liquid market)
- Thai 25% (lower quality Thai rice)
- Thai A.1 (broken rice grade)
- Vietnamese 5% (regional competitor to Thai 5%)

**Data File Location:** `data/raw/external_rice_market/worldbank_pink_sheet/`
**Update Frequency:** Monthly
**Historical Coverage:** July 2008 - December 2024 (198 months)

## Pipeline Scripts

### Primary Analysis Scripts

1. **rice_price_spread_analysis_final.py**
   - Full-featured analysis with configurable start dates
   - Generates comprehensive visualizations and statistics
   - Supports command-line arguments for flexibility
   - Usage: `python data-pipeline/rice_price_spread_analysis_final.py --start-date 2008M07`

2. **rice_price_spread_analysis_working.py**
   - Simplified version for quick analysis
   - Handles missing data gracefully
   - Best for recent data analysis (2022-2024)

### Script Dependencies

The pipeline requires the following Python packages (already in virtual environment):
- pandas (2.3.2): Data manipulation and time series handling
- numpy (2.3.3): Numerical computations
- matplotlib (3.10.6): Visualization generation
- openpyxl (3.1.5): Excel file reading
- requests (2.32.5): Downloading Pink Sheet data

## Output Files

The pipeline generates four types of output files in `data/processed/`:

### 1. Processed Data (CSV)
**Filename Pattern:** `rice_spreads_YYYYMM_YYYYMMDD.csv`
**Contents:**
- Date column (monthly frequency)
- Original prices for all four varieties (USD/mt)
- Absolute spreads vs Thai 5% benchmark (USD/mt)
- Percentage spreads vs Thai 5% (%)
- 12-month moving averages for prices and spreads

### 2. Visualizations (PNG)
**Filename Pattern:** `rice_analysis_comprehensive_YYYYMMDD_HHMMSS.png`
**Contents:**
- Panel 1: Price trends with 12-month moving averages
- Panel 2: Absolute spreads (USD/mt)
- Panel 3: Percentage spreads
- Panel 4: Distribution analysis by year

### 3. Statistical Summary (JSON)
**Filename Pattern:** `rice_statistics_YYYYMMDD_HHMMSS.json`
**Structure:**
```json
{
  "metadata": {
    "analysis_date": "ISO timestamp",
    "start_date": "ISO timestamp",
    "end_date": "ISO timestamp",
    "total_months": integer,
    "data_source": "World Bank Pink Sheet"
  },
  "overall_statistics": {
    "variety_name": {
      "mean": float,
      "median": float,
      "std": float,
      "min": float,
      "max": float,
      "cv": float,
      "valid_months": integer
    }
  },
  "period_analysis": {
    "period_name": {
      "variety_name": {
        "mean": float,
        "volatility": float,
        "months": integer
      }
    }
  },
  "correlation_matrix": {}
}
```

### 4. BigQuery-Ready Data (Optional)
**Filename Pattern:** `rice_spreads_bigquery_YYYYMMDD.csv`
**Additional Columns:**
- ingestion_timestamp
- data_source
- record_id (unique identifier)
- year, month, quarter (partitioning columns)

## Key Findings from Historical Analysis

### Data Quality Metrics
- **Thai 5%**: 198/198 months (100% complete)
- **Thai 25%**: 198/198 months (100% complete)
- **Thai A.1**: 198/198 months (100% complete)
- **Vietnamese 5%**: 197/198 months (99.5% complete)

### Period-Specific Analysis

#### 2008-2009 Global Food Crisis
- **Characteristics**: Extreme price volatility, export restrictions, panic buying
- **Thai 5% Mean**: $581.22/mt (highest among all periods)
- **Volatility**: High across all varieties ($64-88 standard deviation)
- **Key Insight**: Crisis conditions create uniform market pressure across all grades

#### 2010-2011 Recovery Period
- **Characteristics**: Market normalization, rebuilding of stocks
- **Thai 5% Mean**: $515.97/mt
- **Volatility**: Moderate ($52-67 standard deviation)
- **Key Insight**: Gradual return to equilibrium with persistent elevated prices

#### 2012-2015 Stability Period
- **Characteristics**: Normal market functioning, predictable seasonal patterns
- **Thai 5% Mean**: $469.43/mt
- **Vietnamese 5% Volatility**: Notably low ($35 std dev)
- **Key Insight**: Most predictable period for forecasting models

#### 2016-2019 Pre-COVID Baseline
- **Characteristics**: Lowest volatility period, stable trade patterns
- **Thai 5% Mean**: $408.44/mt
- **Volatility**: Minimal ($21-29 standard deviation)
- **Key Insight**: Represents "normal" market conditions for baseline modeling

#### 2020-2022 COVID Disruption
- **Characteristics**: Supply chain issues, changing consumption patterns
- **Thai 5% Mean**: $463.92/mt
- **Volatility**: Moderate increase ($41-48 standard deviation)
- **Key Insight**: Spreads narrowed, suggesting uniform supply constraints

#### 2023-2024 Current Period
- **Characteristics**: Return to elevated prices, climate impacts, geopolitical tensions
- **Thai 5% Mean**: $571.04/mt (approaching crisis levels)
- **Volatility**: Elevated ($48-62 standard deviation)
- **Key Insight**: Market showing stress signals similar to pre-crisis conditions

### Statistical Summary

| Variety | Long-term Mean | Std Dev | CV (%) | Min | Max |
|---------|---------------|---------|--------|-----|-----|
| Thai 5% | $481.76 | $80.03 | 16.6% | $286.00 | $732.00 |
| Thai 25% | $454.38 | $71.98 | 15.8% | $265.00 | $628.00 |
| Thai A.1 | $434.49 | $75.07 | 17.3% | $261.00 | $620.00 |
| Vietnamese 5% | $427.72 | $73.27 | 17.1% | $230.00 | $605.00 |

### Spread Analysis

Average spreads versus Thai 5% benchmark:
- **Thai 25%**: $27.38/mt (5.7% discount)
- **Thai A.1**: $47.27/mt (9.8% discount)
- **Vietnamese 5%**: $54.04/mt (11.2% discount)

These spreads represent quality differentials and remain relatively stable except during crisis periods when they can compress significantly.

## Integration with ERP AI System

### For Time-Series Forecasting Service
The processed data provides:
- Clean, validated price series for model training
- Identified market regimes (crisis, stable, recovery) for regime-switching models
- Volatility measures for risk assessment
- Moving averages for trend identification

### For BigQuery Data Warehouse
The pipeline generates BigQuery-compatible CSV files with:
- Proper date formatting
- Partitioning columns (year, month, quarter)
- Unique record IDs for idempotent loading
- Metadata for data lineage tracking

### For RAG Orchestrator
The statistical summaries and period analyses can be indexed for retrieval when answering queries about:
- Historical price trends
- Market volatility patterns
- Regional price differences
- Crisis period characteristics

## Usage Guidelines

### Running the Analysis

1. **Ensure virtual environment is activated:**
   ```bash
   source venv/bin/activate
   ```

2. **For full historical analysis (recommended):**
   ```bash
   python data-pipeline/rice_price_spread_analysis_final.py --start-date 2008M07
   ```

3. **For recent data only:**
   ```bash
   python data-pipeline/rice_price_spread_analysis_final.py --start-date 2022M01
   ```

4. **For custom output directory:**
   ```bash
   python data-pipeline/rice_price_spread_analysis_final.py --output-dir /custom/path
   ```

### Updating the Data

The World Bank updates the Pink Sheet monthly, typically in the first week of each month. To update:

1. **Force re-download of data:**
   ```bash
   python data-pipeline/rice_price_spread_analysis_final.py --start-date 2008M07 --force-download
   ```

2. **Schedule automated updates:**
   Consider setting up a monthly cron job or Cloud Function to automatically run the pipeline.

### Data Validation Checks

Before using the outputs, verify:
1. Date range covers expected period
2. All four rice varieties have data
3. No extreme outliers (prices > $1000/mt or < $100/mt)
4. Moving averages are smooth without gaps
5. Spread calculations are consistent

## Common Issues and Solutions

### Issue: Missing Thai 5% or Thai 25% data
**Solution:** The script strips whitespace from column names. Ensure the Excel file hasn't been manually edited.

### Issue: Date parsing errors
**Solution:** The script expects 'YYYYMM' format. Check the first column of the Excel file.

### Issue: Memory errors with long time series
**Solution:** Process in chunks or increase system memory allocation.

### Issue: Visualization layout problems
**Solution:** The warning about tight_layout is cosmetic and doesn't affect the output quality.

## Maintenance and Updates

### Monthly Tasks
- Download latest Pink Sheet data
- Run analysis pipeline
- Verify output quality
- Update BigQuery tables

### Quarterly Tasks
- Review period definitions for analysis
- Update volatility thresholds if market conditions change
- Archive old processed files

### Annual Tasks
- Review and update statistical baselines
- Recalibrate forecasting models with new data
- Document any structural changes in rice markets

## Contact and Support

For questions about this pipeline or issues with the analysis:
1. Check this documentation first
2. Review the script comments for implementation details
3. Consult the World Bank Pink Sheet methodology documentation
4. Raise issues in the project GitHub repository

## Version History

- **v1.0.0** (2024-09-26): Initial implementation with 2022-2024 data
- **v2.0.0** (2024-09-26): Extended to handle 2008-2024 historical data
- **v2.1.0** (2024-09-26): Added period-specific analysis and comprehensive statistics

---
*Last Updated: September 26, 2024*
*Maintained by: ERP AI Data Pipeline Team*
