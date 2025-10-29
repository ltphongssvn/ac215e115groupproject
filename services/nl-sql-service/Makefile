# services/nl-sql-service/Makefile
.PHONY: build run test clean docker-build docker-run

# Build Docker image
build:
	docker build -t nl-sql-service:latest .

# Run containerized service
run: build
	docker run --rm --env-file .env -p 8001:8001 nl-sql-service:latest

# Run with database initialization
run-with-db: build
	psql "postgresql://rice_admin:localdev123@34.45.44.214:5432/rice_market_db" < create_tables.sql
	docker run --rm --env-file .env -p 8001:8001 nl-sql-service:latest

# Run tests
test:
	docker run --rm nl-sql-service:latest pytest tests/

# Clean up
clean:
	docker rmi nl-sql-service:latest 2>/dev/null || true

# Development setup
dev-setup:
	uv venv
	uv pip install -e .
