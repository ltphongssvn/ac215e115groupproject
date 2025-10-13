# Rice Market AI - Full Migration Pipeline

## Overview
This pipeline performs a complete end-to-end data migration:
1. Cleans GCP Cloud SQL database
2. Rebuilds Docker containers from scratch
3. Syncs data from Airtable to local Docker PostgreSQL
4. Migrates data from Docker to GCP Cloud SQL

## Prerequisites

### Required Software
- Python 3.11+
- Docker Desktop
- PostgreSQL client (`psql`)
- Google Cloud SDK (`gcloud`)

### Required Files (Get from Team Lead)
1. `data-pipeline/.env` - Local Docker configuration
2. `data-pipeline/.env.gcp` - GCP Cloud SQL configuration

## Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/ltphongssvn/ac215e115groupproject.git
cd ac215e115groupproject
```

### 2. Install Dependencies
```bash
pip install -r data-pipeline/requirements.txt
```

### 3. Create Environment Files
Get the secure credentials from your team lead and create:

```bash
# Local Docker config
cp data-pipeline/.env.example data-pipeline/.env
# Edit with actual credentials

# GCP config
cp data-pipeline/.env.gcp.example data-pipeline/.env.gcp
# Edit with actual credentials
```

### 4. Authenticate with GCP
```bash
gcloud auth login
gcloud config set project erp-for-smes
```

### 5. Run Pipeline
```bash
python data-pipeline/pipeline_full_migration.py
```

## Expected Output
- Total duration: ~17 minutes
- Records processed: 13,818
- Tables synced: 8 (customers, commodities, contracts, shipments, etc.)

## Troubleshooting

### Docker Build Issues
If Docker build fails, ensure Dockerfile.postgres exists:
```bash
ls -la Dockerfile.postgres
```

### GCP Connection Issues
Test GCP connection:
```bash
psql -h <GCP_IP> -U rice_admin -d rice_market_db -c "SELECT 1;"
```

### Airtable API Issues
If rate limited, increase RATE_LIMIT_DELAY in .env files.

## Security Notes
- NEVER commit .env or .env.gcp files
- These files are in .gitignore
- Share credentials securely via encrypted channels only
