#!/usr/bin/env python3
# data-pipeline/sync_production_ready_configured.py
# Production-ready synchronization script with proper configuration

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
# This needs to happen before importing sync_ultimate
load_dotenv('data-pipeline/.env')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_ultimate import *

class CompleteProductionSync(UltimateProductionPostgreSQLSync):
    """
    The complete synchronization class with all mappings discovered through our journey.
    This class represents the accumulation of all our debugging efforts. Each mapping
    tells a story about a specific challenge we encountered and solved together.
    """
    
    def __init__(self, config: SyncConfig):
        super().__init__(config)

# Entry point - this is what actually runs the synchronization
if __name__ == "__main__":
    print("Starting AirTable to PostgreSQL synchronization...")
    print("=" * 70)
    
    # Load configuration from environment variables
    airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
    airtable_api_key = os.getenv('AIRTABLE_API_KEY')
    
    if not airtable_base_id or not airtable_api_key:
        print("ERROR: Missing required environment variables")
        print(f"AIRTABLE_BASE_ID: {'Set' if airtable_base_id else 'Not set'}")
        print(f"AIRTABLE_API_KEY: {'Set' if airtable_api_key else 'Not set'}")
        sys.exit(1)
    
    print(f"Using AirTable Base: {airtable_base_id}")
    print(f"API Key: {'*' * 10} (hidden for security)")
    
    try:
        # Create configuration for the sync with the required parameters
        config = SyncConfig(
            airtable_base_id=airtable_base_id,
            airtable_api_key=airtable_api_key
        )
        
        print("Configuration created successfully")
        
        # Create and run the synchronization
        sync = CompleteProductionSync(config)
        print("Sync object created successfully")
        
        # Call whatever method starts the sync - typically run() or sync()
        if hasattr(sync, 'run'):
            print("Calling sync.run() method...")
            result = sync.run()
            print(f"Sync completed with result: {result}")
        elif hasattr(sync, 'sync'):
            print("Calling sync.sync() method...")
            result = sync.sync()
            print(f"Sync completed with result: {result}")
        elif hasattr(sync, 'execute'):
            print("Calling sync.execute() method...")
            result = sync.execute()
            print(f"Sync completed with result: {result}")
        else:
            print("ERROR: Could not find sync execution method")
            available_methods = [m for m in dir(sync) if not m.startswith('_')]
            print("Available methods:", available_methods[:15])
            
    except Exception as e:
        print(f"ERROR during synchronization: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 70)
    print("Synchronization process ended")
