# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/README.md

# Data Pipeline - Complete Documentation

## Overview
This is the consolidated documentation for the Rice Market AI data pipeline system. The pipeline handles end-to-end data flow from Airtable to PostgreSQL, integrates market factors and weather data, and prepares datasets for ML time-series forecasting.

## Quick Start

### Primary Pipeline Script
```bash
python data-pipeline/pipeline_full_migration.py
```

This script orchestrates the complete data migration including:
1. Cleans GCP Cloud SQL database
2. Rebuilds Docker containers from scratch
3. Syncs data from Airtable to local Docker PostgreSQL
4. Migrates data from Docker to GCP Cloud SQL

---

## Part 1: Airtable → PostgreSQL Sync

### Configuration
Environment variables (`.env` file):
```bash
AIRTABLE_API_KEY=***
AIRTABLE_BASE_ID=***
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DATABASE=rice_market_db
POSTGRES_USER=rice_admin
POSTGRES_PASSWORD=localdev123
POSTGRES_SCHEMA=airtable_sync
SYNC_MODE=incremental
RATE_LIMIT_DELAY=0.25
```

### Key Features
- **Table ID Support**: Prevents 403 errors on protected bases
- **Column Sanitization**: Ensures DB-safe identifiers
- **NaN Handling**: Converts Airtable `{"specialValue":"NaN"}` to SQL NULL
- **Percent Normalization**: Converts "85%" → 0.85 for numeric fields
- **Incremental Sync**: Supports `IS_AFTER(LAST_MODIFIED_TIME())`

### Running Sync Operations
```bash
# Full sync
SYNC_MODE=full python data-pipeline/pipeline_full_migration.py

# Incremental sync (default)
python data-pipeline/pipeline_full_migration.py
```

---

## Part 2: Full Migration Pipeline

### Prerequisites
- Python 3.11+
- Docker Desktop
- PostgreSQL client (`psql`)
- Google Cloud SDK (`gcloud`)

### Migration Process
1. **Clean GCP Cloud SQL database**
2. **Rebuild Docker containers from scratch**
3. **Sync from Airtable to Docker PostgreSQL**
4. **Migrate to GCP Cloud SQL**

### Setup Instructions

1. **Clone Repository**:
```bash
git clone https://github.com/ltphongssvn/ac215e115groupproject.git
cd ac215e115groupproject
```

2. **Install Dependencies**:
```bash
pip install -r data-pipeline/requirements.txt
```

3. **Configure Environment Files**:
```bash
# Local Docker config
cp data-pipeline/.env.example data-pipeline/.env
# Edit with actual credentials

# GCP config
cp data-pipeline/.env.gcp.example data-pipeline/.env.gcp
# Edit with actual credentials
```

4. **Authenticate GCP**:
```bash
gcloud auth login
gcloud config set project erp-for-smes
```

5. **Run Migration**:
```bash
python data-pipeline/pipeline_full_migration.py
```

### Expected Results
- Duration: ~17 minutes
- Records: 13,818
- Tables: 8 (customers, commodities, contracts, shipments, etc.)

---

## Part 3: Rice Market Analysis Dataset

### Dataset Overview
**Output**: `/data/integrated/rice_market_rainfall_complete_YYYYMMDD_HHMMSS.csv`
- **Variables**: 21 columns
- **Records**: 198 monthly observations
- **Period**: July 2008 - December 2024
- **Purpose**: ML time-series price forecasting

### Data Components

#### Rice Price Data (Target Variables)
- **Thai 5%**: Premium grade benchmark
- **Thai 25%**: Standard grade
- **Thai A.1 Super**: Economy grade
- **Vietnamese 5%**: Regional competitor

#### Market Factors
- **Energy**: Oil prices (Dubai/Oman Crude)
- **Macroeconomic**: Inflation, Population growth/total
- **Climate**: ENSO Index (Niño 3.4)
- **Agricultural**: Fertilizer composite prices

#### Weather Integration
- **Asia Average Rainfall**: mm/month
- **Rainfall Anomaly**: % deviation from mean

### Correlation Analysis Results

**Strong Predictors (>0.35)**:
- Inflation → Rice Prices: 0.426
- Oil Prices → Rice Prices: 0.388
- Fertilizer → Rice Prices: 0.374

**Lag-Effect Variables**:
- Rainfall → Rice Prices: 0.054
- ENSO → Rice Prices: -0.074

### Pipeline Architecture

#### Stage 1: Data Collection
- API authentication and rate limiting
- Format standardization
- Temporal alignment

#### Stage 2: Processing
- PII scrubbing
- Missing value handling
- Outlier detection
- Feature engineering

#### Stage 3: Integration
- Temporal joins
- Validation checks
- Correlation analysis
- Metadata generation

---

## Database Schema Management

### Schema Hardening
```sql
-- Numeric type enforcement
ALTER TABLE airtable_sync.commodities
  ALTER COLUMN average_unit_price_from_contracts TYPE NUMERIC(12,3),
  ALTER COLUMN total_contracted_quantity_kg TYPE NUMERIC(18,3);

-- Non-negative constraints
ALTER TABLE airtable_sync.commodities
  ADD CONSTRAINT commodities_avg_price_nonneg
    CHECK (average_unit_price_from_contracts >= 0),
  ADD CONSTRAINT commodities_total_qty_nonneg
    CHECK (total_contracted_quantity_kg >= 0);
```

### Verification Queries

#### Check for JSON NaN artifacts:
```sql
CREATE FUNCTION airtable_sync.find_json_nan()
RETURNS TABLE (out_table_name text, out_column_name text, matches int)
LANGUAGE plpgsql AS $$
-- Function body
$$;

SELECT * FROM airtable_sync.find_json_nan();
-- Expected: 0 rows
```

#### Commodities health check:
```sql
SELECT COUNT(*) FILTER (WHERE average_unit_price_from_contracts IS NOT NULL) AS nonnull_prices,
       MIN(average_unit_price_from_contracts) AS min_price,
       AVG(average_unit_price_from_contracts) AS avg_price
FROM airtable_sync.commodities;
```

---

## ML Pipeline Integration

### Feature Store (BigQuery + Feast)
- **Feature Registry**: 21 variables with versioning
- **Online Store**: Real-time serving
- **Offline Store**: Training data
- **Feature Consistency**: Training-serving parity

### Model Training Support
- Time-series cross-validation
- Feature scaling and normalization
- Lag feature generation
- Missing value strategies

### Data Quality Metrics
- **Completeness**: 100% for all core variables
- **Temporal Coverage**: 16.5 years monthly
- **Economic Events Captured**: 2008 crisis, 2011 Thai floods, 2015-16 El Niño, COVID-19, 2022 Ukraine conflict

---

## Troubleshooting

### Common Issues

**Docker Build Failures**:
```bash
ls -la Dockerfile.postgres
docker build -f Dockerfile.postgres -t postgres-rice:latest .
```

**GCP Connection Issues**:
```bash
psql -h <GCP_IP> -U rice_admin -d rice_market_db -c "SELECT 1;"
```

**Airtable Rate Limiting**:
Increase `RATE_LIMIT_DELAY` in `data-pipeline/.env`

**Numeric Overflow Errors**:
Check for malformed percent inputs, verify normalization logic

---

## Operational Checklist

1. **Pre-deployment**:
    - [ ] Run full sync in staging
    - [ ] Verify no JSON NaN artifacts
    - [ ] Check numeric value ranges
    - [ ] Validate correlation metrics

2. **Deployment**:
    - [ ] Backup existing data
    - [ ] Run pipeline_full_migration.py
    - [ ] Verify record counts
    - [ ] Test downstream services

3. **Post-deployment**:
    - [ ] Monitor error logs
    - [ ] Verify ML model inputs
    - [ ] Check API response times
    - [ ] Validate dashboard updates

---

## Security Notes
- NEVER commit `data-pipeline/.env` or `data-pipeline/.env.gcp` files
- These files are in .gitignore
- Share credentials securely via encrypted channels only
- Use encrypted channels for credential sharing
- Rotate API keys quarterly
- Monitor access logs for anomalies

---

## Support

For issues or questions:
- Check logs in `/data-pipeline/logs/`
- Review archived scripts in `/data-pipeline/archive/`
- Contact the Data Engineering team

Last Updated: October 13,  2024