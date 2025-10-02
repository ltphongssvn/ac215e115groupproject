#!/usr/bin/env python3
# data-pipeline/sync_explorer.py
# Explores the actual synchronization methods available

import os
import sys
import inspect
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('data-pipeline/.env')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_ultimate import *

# Entry point
if __name__ == "__main__":
    print("Exploring Synchronization Methods")
    print("=" * 70)
    
    # Load configuration from environment variables
    airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
    airtable_api_key = os.getenv('AIRTABLE_API_KEY')
    
    if not airtable_base_id or not airtable_api_key:
        print("ERROR: Missing required environment variables")
        sys.exit(1)
    
    try:
        # Create configuration and sync object
        config = SyncConfig(
            airtable_base_id=airtable_base_id,
            airtable_api_key=airtable_api_key
        )
        
        # Try to use UltimateProductionPostgreSQLSync directly
        sync = UltimateProductionPostgreSQLSync(config)
        
        print("Sync object created successfully")
        print("\nAnalyzing available methods:")
        print("-" * 40)
        
        # Examine key methods
        key_methods = ['upsert_records', 'sync_relationships', 'get_last_sync_time']
        
        for method_name in key_methods:
            if hasattr(sync, method_name):
                method = getattr(sync, method_name)
                sig = inspect.signature(method)
                print(f"\n{method_name}:")
                print(f"  Signature: {sig}")
                if method.__doc__:
                    print(f"  Docstring: {method.__doc__[:200]}")
        
        print("\n" + "-" * 40)
        print("\nAttempting to check for synchronization method in parent classes...")
        
        # Check if there's a sync_all or similar method
        all_methods = [m for m in dir(sync) if not m.startswith('_')]
        sync_methods = [m for m in all_methods if 'sync' in m.lower() or 'run' in m.lower() or 'execute' in m.lower()]
        
        print(f"Methods containing 'sync', 'run', or 'execute': {sync_methods}")
        
        # Try to find the main synchronization entry point
        if 'sync_all' in all_methods:
            print("\nFound sync_all method!")
            sig = inspect.signature(sync.sync_all)
            print(f"Signature: {sig}")
        
        # Check for process or start methods
        process_methods = [m for m in all_methods if 'process' in m.lower() or 'start' in m.lower()]
        if process_methods:
            print(f"\nMethods containing 'process' or 'start': {process_methods}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
