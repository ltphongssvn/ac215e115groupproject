# RAG Orchestrator Service
# Path: /services/rag-orchestrator/README.md

## Overview
Retrieval-Augmented Generation service using Vertex AI Agent Builder and Vector Search.
Provides intelligent document summarization and information extraction from rice market documents.

## Directory Structure
- `src/api/` - REST endpoints for document upload and query handling
- `src/core/` - RAG pipeline orchestration and ranking logic
- `src/models/` - Embedding models and generation interfaces
- `src/utils/` - Document processing and vector operations
- `tests/unit/` - Unit tests for RAG components
- `tests/integration/` - Integration tests with Vector Search
- `config/` - Service configuration and prompts
- `docs/` - Service documentation and API specs
- `scripts/` - Data ingestion and indexing scripts

## Tech Stack
- Vertex AI Agent Builder
- Vertex AI Vector Search
- Cloud SQL with pgvector
- Document AI for processing
- textembedding-gecko@003
- FastAPI
- Cloud Run

## Team Owner
RAG-Based Document Summarization Team
