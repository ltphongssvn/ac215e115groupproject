# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data/README.md
# Data Directory Structure and Guidelines

## Overview

This directory contains all data files used by the ERP AI system's microservices. The data is organized into three categories to maintain clear data lineage and support reproducible analysis.

## Directory Structure

```
data/
├── raw/                 # Original, immutable data files
│   └── sme_rice_associations/
│       └── sme_rice_associations_asia_expanded_regions_v6.csv
├── processed/          # Cleaned and transformed data ready for model consumption
└── interim/           # Intermediate transformations for complex processing pipelines
```

## Data Categories

### Raw Data (`/raw`)
Original data files exactly as received from sources. These files should NEVER be modified. If corrections are needed, create processed versions instead.

**Current Raw Datasets:**
- **SME Rice Associations Asia Dataset** (`sme_rice_associations_asia_expanded_regions_v6.csv`)
  - Purpose: Source data for time-series forecasting of rice prices across Asian markets
  - Contents: Rice association information across expanded Asian regions
  - Used by: Time-Series Forecasting Service
  - Format: CSV
  - Update frequency: Static reference data
  - File size: [To be updated after inspection]

### Processed Data (`/processed`)
Clean, transformed data ready for consumption by our services. Files here are generated from raw data through documented transformation pipelines.

### Interim Data (`/interim`)
Temporary files created during multi-step processing pipelines. Useful for debugging and understanding data transformations.

## Guidelines for Data Management

### Adding New Data Files

When adding new data sources:

1. **Always place original files in `/raw`** with a descriptive subdirectory
2. **Document the data source** in this README including:
   - Purpose and description
   - Source/origin of the data
   - Which service(s) use it
   - Update frequency
   - Any special considerations
3. **Create a processing script** if transformation is needed
4. **Consider file size** - if over 100MB, consider using Git LFS or external storage

### Git Considerations

**Important:** Large data files (>50MB) should not be committed directly to Git. Instead:

1. For files 50-100MB: Use Git Large File Storage (LFS)
2. For files >100MB: Store externally and document the location
3. Always commit a README or metadata file describing the data

### Data Processing Pipeline

For the SME Rice Associations data:

```python
# Example processing pipeline (to be implemented in data-pipeline/)
# 1. Read raw CSV from data/raw/sme_rice_associations/
# 2. Clean and validate data
# 3. Add calculated fields needed for forecasting
# 4. Save to data/processed/ for model consumption
```

### Accessing Data in Services

Services should follow this pattern for data access:

```python
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/services/ts-forecasting/data_loader.py
import os
import pandas as pd
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

def load_rice_associations_data():
    """Load processed SME rice associations data for forecasting."""
    processed_file = DATA_DIR / "processed" / "sme_rice_associations_cleaned.csv"
    
    if not processed_file.exists():
        # Fall back to raw data if processed doesn't exist
        raw_file = DATA_DIR / "raw" / "sme_rice_associations" / "sme_rice_associations_asia_expanded_regions_v6.csv"
        print(f"Warning: Using raw data from {raw_file}")
        return pd.read_csv(raw_file)
    
    return pd.read_csv(processed_file)
```

## Data Security and Privacy

**Critical:** Before committing any data:

1. **Check for PII** (Personally Identifiable Information)
2. **Verify data sharing permissions** 
3. **Apply necessary anonymization** if required
4. **Never commit credentials or API keys**

## Current Data Inventory

| Dataset | Type | Size | Last Updated | Service | Status |
|---------|------|------|--------------|---------|--------|
| SME Rice Associations Asia v6 | Reference | TBD | 2024-09-17 | TS Forecasting | Active |

## Processing Scripts

Processing scripts for each dataset should be placed in `/data-pipeline/` with clear naming:

- `process_sme_rice_associations.py` - Processes rice association data for forecasting

## Environment Variables

Services requiring data paths should use environment variables:

```env
# Add to .env file
DATA_RAW_PATH=/app/data/raw
DATA_PROCESSED_PATH=/app/data/processed
RICE_ASSOCIATIONS_FILE=sme_rice_associations_asia_expanded_regions_v6.csv
```

## Maintenance

- **Weekly:** Review interim folder and clean unnecessary files
- **Monthly:** Validate all processing pipelines still work
- **Quarterly:** Archive old raw data files no longer in use

---
*Last updated: September 17, 2024*  
*Data steward: Time-Series Forecasting Team*