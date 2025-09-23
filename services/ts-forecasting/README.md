# Time-Series Forecasting Service
# Path: /services/ts-forecasting/README.md

## Overview
ML-powered price forecasting service using LSTM/Prophet ensemble models on Vertex AI.
Generates interpretable 6-month price predictions for rice market operations.

## Directory Structure
- `src/api/` - Prediction endpoints and result formatting
- `src/core/` - Forecasting pipeline and feature engineering
- `src/models/` - LSTM/Prophet models and ensemble logic
- `src/utils/` - Time-series utilities and SHAP explainability
- `tests/unit/` - Unit tests for forecasting components
- `tests/integration/` - Integration tests with BigQuery
- `config/` - Model configurations and hyperparameters
- `docs/` - Model documentation and performance metrics
- `scripts/` - Training and evaluation scripts

## Tech Stack
- Vertex AI Custom Training
- PyTorch LSTM models
- Prophet for time-series
- BigQuery with Feast Feature Store
- MLflow Model Registry on Vertex AI
- SHAP for explainability
- FastAPI
- Cloud Run

## Team Owner
Time-Series Price Forecasting Team
