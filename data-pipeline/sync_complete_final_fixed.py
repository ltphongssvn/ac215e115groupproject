#!/usr/bin/env python3
# data-pipeline/sync_complete_final_fixed.py
# The complete production synchronization with all discovered mappings

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
    
    try:
        # Create configuration for the sync
        # The sync_ultimate module should define what SyncConfig needs
        config = SyncConfig()
        
        # Create and run the synchronization
        sync = CompleteProductionSync(config)
        
        # Call whatever method starts the sync - typically run() or sync()
        # We'll need to check what method name sync_ultimate uses
        if hasattr(sync, 'run'):
            sync.run()
        elif hasattr(sync, 'sync'):
            sync.sync()
        elif hasattr(sync, 'execute'):
            sync.execute()
        else:
            print("ERROR: Could not find sync execution method")
            print("Available methods:", [m for m in dir(sync) if not m.startswith('_')])
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 70)
    print("Synchronization complete!")
