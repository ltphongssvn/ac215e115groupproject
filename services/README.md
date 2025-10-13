# Microservices Architecture

## Overview
This directory contains three microservices that form the core ML/AI pipeline:

1. **NL-SQL Service** (port 8001) - Natural language to SQL query conversion
2. **RAG Orchestrator** (port 8002) - Agentic graph-based RAG with 4-layer memory
3. **TS Forecasting** (port 8003) - Time series forecasting with 7 models

## Quick Start

### Start All Services
```bash
python services/start_all_microservices.py
```

This script:
- Stops any running containers
- Builds Docker images for all services
- Starts containers with health checks
- Runs comprehensive test suites
- Reports final status

### Expected Output

**Build Phase:**
```
Building nl-sql-service:latest...
Building rag-orchestrator:latest...
Building ts-forecasting:latest...
```

**Health Checks:**
```
✅ NL-SQL Service - HEALTHY
✅ RAG Orchestrator - HEALTHY  
✅ TS Forecasting - HEALTHY
Healthy: 3/3
```

**Test Results:**
```
NL-SQL Service:    4/4 tests passed
RAG Orchestrator:  6/6 tests passed
TS Forecasting:    9/9 tests passed
-----------------------------------
Total:            19/19 tests passed ✅
```

## Service Details

### NL-SQL Service
- **Endpoint:** `http://localhost:8001`
- **Function:** Converts natural language queries to SQL
- **Tech:** FastAPI, LangChain, PostgreSQL
- **Tests:** Query validation, SQL generation, error handling

### RAG Orchestrator
- **Endpoint:** `http://localhost:8002`
- **Function:** Agentic RAG with graph memory (episodic, semantic, procedural, temporal)
- **Tech:** FastAPI, LangGraph, Vector DB, uv
- **Tests:** Standard queries, temporal queries, workflow storage

### TS Forecasting
- **Endpoint:** `http://localhost:8003`
- **Function:** Multi-model time series forecasting
- **Models:** ARIMA, SARIMA, Prophet, LSTM, TimeGPT, Chronos, Moirai
- **Tech:** FastAPI, pandas, statsmodels, PyTorch, uv
- **Tests:** All 7 models + health check

## Architecture

```
                ┌─────────────────┐
                │        Frontend UI   │
                └────────┬────────┘
                            │
                     ┌────┴────┐
                     │   API GW   │
                     └────┬────┘
                            │
    ┌────┴──────────────────────────────┐
    │                       │				    	│
┌───▼───────┐  ┌──────▼─────┐  ┌───────▼──────┐
│  NL-SQL       │  │    RAG         │  │ TS Forecast      │
│  :8001        │  │  :8002         │  │   :8003          │
└───────────┘  └────────────┘  └──────────────┘
```

## Development

### Individual Service Testing
```bash
# Test specific service
pytest services/nl-sql-service/tests/
pytest services/rag-orchestrator/tests/
pytest services/ts-forecasting/tests/unit/
```

### Docker Commands
```bash
# View logs
docker logs nl-sql-service
docker logs rag-orchestrator
docker logs ts-forecasting

# Stop services
docker stop nl-sql-service rag-orchestrator ts-forecasting

# Remove containers
docker rm nl-sql-service rag-orchestrator ts-forecasting
```

## Troubleshooting

**Port conflicts:**
```bash
# Check ports
lsof -i :8001 -i :8002 -i :8003

# Kill processes
docker stop $(docker ps -q)
```

**Build failures:**
- Clear Docker cache: `docker system prune -a`
- Check disk space: `df -h`
- Verify requirements.txt files

**Test failures:**
- Check service health endpoints first
- Review Docker logs for errors
- Ensure all dependencies installed

## Requirements

- Python 3.11+
- Docker Desktop
- 8GB+ RAM
- Ports 8001-8003 available

## Latest Test Results (2025-10-12)

All services operational with 19/19 tests passing:
- ✅ NL-SQL: 4 passed
- ✅ RAG: 6 passed  
- ✅ TS Forecasting: 9 passed

No warnings or errors.
** Document microservices architecture and test results.
