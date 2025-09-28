# Rice Market Data Pipeline

Production-ready synchronization system between AirTable and PostgreSQL for rice market operations.

## Quick Start

```bash
# Test connections
python src/connection_test.py

# Run synchronization
python src/sync_production.py
```

## Project Structure

```
data-pipeline/
├── src/                    # Production source code
│   ├── sync_production.py  # Main synchronization script
│   ├── core_sync.py        # Core synchronization logic
│   ├── connection_test.py  # Database connection tester
│   └── discovery/          # Schema discovery tools
├── sql/                    # Database schemas and migrations
│   ├── 01_schema.sql       # Main database schema
│   └── 02_read_replica_setup.sql
├── config/                 # Configuration files
│   └── postgresql.conf
├── logs/                   # Synchronization logs and reports
├── data/                   # Data files and schemas
│   └── schemas/           # JSON schema definitions
├── archive/               # Historical development files
└── docs/                  # Documentation
```

## Configuration

1. Copy `.env.example` to `.env`
2. Set your AirTable API key
3. Configure PostgreSQL connection settings

## Features

- Vietnamese character handling
- Automatic data validation and transformation
- Incremental synchronization support
- Comprehensive error handling and logging
- Column name mapping for schema inconsistencies

## Data Model

- 105 customers
- 45 commodities  
- 3,248 contracts
- 383 shipments
- 8,342 inventory movements
- 1,690 finished goods records

## Monitoring

Check `logs/sync_report_final.txt` for the latest synchronization report.

---
Developed through iterative debugging with real production data.
