# /home/lenovo/code/ltphongssvn/ac215e115groupproject/README.md

# ERP AI Architecture Implementation for AC215/E115
## Rice Market AI System - Natural Language SQL, RAG, and Time-Series Forecasting

📚 **[View Complete Project Documentation](docs/DOCUMENTATION_INDEX.md)**

This project implements a comprehensive Enterprise Resource Planning (ERP) AI system for rice market operations, leveraging cutting-edge AI technologies for natural language interfaces, document understanding, and predictive analytics.

## Quick Links
- 📖 [Documentation Index](docs/DOCUMENTATION_INDEX.md)
- 🚀 [Getting Started](docs/onboarding/github-collaboration-guide.md)
- 📋 [Statement of Work](docs/milestones/ms1/Statement%20of%20Work-%20Rice%20Market%20AI%20System_Rev.04.pdf)
- 👥 [Milestones](docs/milestones/)

## Core Capabilities

1. **Natural Language to SQL (NL+SQL) Agent**: Query ERP databases using natural language
2. **RAG-Based Document Summarization**: Intelligent document analysis with vector search and LLM generation
3. **Time-Series Price Forecasting**: 6-month price predictions using LSTM/Prophet ensemble models

## Architecture

```
ac215e115groupproject/
├── api-gateway/              # Kong/Nginx API gateway
├── services/
│   ├── nl-sql-agent/        # Natural language to SQL service
│   ├── rag-orchestrator/    # Document retrieval and generation
│   └── ts-forecasting/      # Time-series prediction
├── infrastructure/
│   ├── docker/              # Docker configurations
│   ├── kubernetes/          # K8s manifests
│   └── terraform/           # Infrastructure as Code
├── data-pipeline/           # ETL and data ingestion
└── ml-services/            # Vertex AI Pipelines
```

## Technology Stack

- **Core**: Python 3.12+, FastAPI, Cloud Run, Cloud SQL (PostgreSQL), Redis
- **AI/ML**: LangChain, Vertex AI (Gemini 1.5 Pro), Vector Search, PyTorch, Prophet
- **Infrastructure**: Google Cloud Platform, Kubernetes (GKE), GitHub Actions

## Quick Start

### Prerequisites
- Ubuntu 24.04 LTS or compatible (WSL2 supported)
- Python 3.12+
- Docker 28.0+
- Git

### Development Setup

1. **Clone and navigate**
```bash
git clone https://github.com/ltphongssvn/ac215e115groupproject.git
cd ac215e115groupproject
```

2. **Python environment** (choose one)
```bash
# venv (recommended for beginners)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/dev.txt

# conda
conda create -n ac215project python=3.12
conda activate ac215project
pip install -r requirements/dev.txt

# uv (fastest)
uv venv
source .venv/bin/activate
uv pip install -r requirements/dev.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configurations
```

4. **Start Docker services**
```bash
docker compose up -d
```

5. **Verify installation**
```bash
curl http://localhost:8000/health
```

## Docker Environment

### Services
- **PostgreSQL**: Port 5433, Database: rice_market_db
- **Redis**: Port 6380, Caching layer
- **pgAdmin**: http://localhost:5050 (admin@example.com/admin123)
- **Adminer**: http://localhost:8081

### Database Setup

The PostgreSQL container auto-initializes with schema from `data-pipeline/schema/postgresql_ddl.sql`, containing:
- 8 core tables (customers, commodities, contracts, shipments, etc.)
- 13,638 records representing Vietnamese rice trading operations
- Specialized fields for warehouse locations (BX prefixes) and quality metrics

### Data Synchronization (Optional)

**Security Note**: Never commit API keys. Use `.env` files (gitignored).

1. **Setup credentials**
```bash
cp data-pipeline/.env.example data-pipeline/.env
# Add AIRTABLE_API_KEY and AIRTABLE_BASE_ID
```

2. **Run sync**
```bash
# Full sync (first time)
SYNC_MODE=full python data-pipeline/pipeline_complete_from_source.py

# Incremental sync
python data-pipeline/pipeline_complete_from_source.py
```

## Testing

```bash
# Unit tests
cd services/nl-sql-agent
pytest tests/

# Integration tests
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Load testing
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Performance Metrics

| Operation | Traditional | Optimized | Improvement |
|-----------|------------|-----------|-------------|
| Package Install | 5-10s | 398ms | 12-25x |
| Docker Rebuild | 30+s | 1.6s | 18x |
| Service Startup | 10-15s | <5s | 2-3x |

## Development Status

### Completed ✅
- Python environment foundation with multi-manager support
- Docker containerization with health checks
- FastAPI test service with Swagger UI
- Database schema and migration pipeline

### Current Sprint 🚀
- Milestone 1: Project Proposal (Due: 2025-09-25)

### Upcoming 📅
- Milestone 2: Infrastructure & Containerization (2025-10-16)
- Milestone 3: Midterm Presentation (2025-10-28)
- Milestone 4: Full-Stack Development (2025-11-25)
- Milestone 5: Deployment & Scaling (2025-12-11)

## Troubleshooting

### Port Conflicts
Modify ports in docker-compose.yml if defaults are in use

### Database Issues
```bash
docker compose logs postgres | grep ERROR
docker exec rice_market_postgres pg_isready -U rice_admin
```

### Airtable Sync
- Verify API key format (starts with 'pat')
- Check network connectivity
- Respect rate limits (5 req/sec)

## Security Best Practices

- Never commit credentials
- Use environment variables for configuration
- Different credentials per environment
- Rotate keys regularly
- Apply least privilege principle

## Contributing

1. Create feature branch from `develop`
2. Follow coding standards (Black, mypy, type hints)
3. Include tests
4. Submit PR with clear description

## Team

- **Thanh Phong Le**
- **Davar Jamali**
- **Pranab Nepal**

## Support

- Team members: Check troubleshooting, review logs
- Reviewers: Docker environment works without API keys, request demos for sync

---

*Active development - check regularly for updates*
