.PHONY: help install test sync clean

help:
	@echo "Rice Market Data Pipeline Commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make sync     - Run synchronization"
	@echo "  make test     - Test database connections"
	@echo "  make clean    - Clean logs and cache"

install:
	pip install -r requirements.txt

sync:
	python src/sync_production.py

test:
	python src/connection_test.py

clean:
	rm -rf __pycache__ src/__pycache__ src/discovery/__pycache__
	rm -f logs/*.log logs/sync_report*.txt

logs:
	tail -f logs/sync.log
