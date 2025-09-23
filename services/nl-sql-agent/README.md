# NL+SQL Agent Service
# Path: /services/nl-sql-agent/README.md

## Overview
Natural Language to SQL translation service using Vertex AI Gemini 1.5 Pro and LangChain.
Enables users to query the Rice Market ERP database using conversational language.

## Directory Structure
- `src/api/` - FastAPI endpoints for NL query handling
- `src/core/` - Business logic for SQL generation and validation
- `src/models/` - Vertex AI Gemini integration and LLM interfaces
- `src/utils/` - Helper functions for query sanitization and formatting
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests with Cloud SQL
- `config/` - Service configuration files
- `docs/` - Service-specific documentation
- `scripts/` - Utility scripts for development and deployment

## Tech Stack
- Vertex AI Gemini 1.5 Pro
- LangChain with LangGraph StateGraph
- Cloud SQL PostgreSQL
- FastAPI
- Cloud Run

## Team Owner
Natural Language SQL (NL+SQL) Team
