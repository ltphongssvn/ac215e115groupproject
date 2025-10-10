#!/bin/bash
# Rice Market Data Pipeline Runner

echo "Rice Market Data Synchronization"
echo "================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the synchronization
python src/sync_production.py

echo ""
echo "Synchronization complete. Check logs/sync_report_final.txt for details."
