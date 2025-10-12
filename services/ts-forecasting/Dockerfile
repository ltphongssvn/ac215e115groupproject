# services/ts-forecasting/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

COPY services/ts-forecasting/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY services/ts-forecasting/src/ ./src/
COPY services/ts-forecasting/tests/ ./tests/
COPY data/integrated/rice_market_rainfall_complete_20251010_062253.csv ./data/integrated/

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8003"]
