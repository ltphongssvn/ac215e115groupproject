#!/usr/bin/env python3
# File path: ~/code/ltphongssvn/ac215e115groupproject/run_sync.py
# Wrapper script to properly load environment variables before running sync

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load the .env file from data-pipeline directory
# This MUST happen before any imports that might check for environment variables
env_path = Path(__file__).parent / 'data-pipeline' / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment from: {env_path}")
else:
    print(f"ERROR: .env file not found at {env_path}")
    sys.exit(1)

# Verify the API key is loaded
api_key = os.getenv('AIRTABLE_API_KEY')
if not api_key:
    print("ERROR: AIRTABLE_API_KEY not found in environment after loading .env")
    sys.exit(1)
else:
    # Only show first/last 4 chars for security
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
    print(f"API Key loaded: {masked_key}")

# Add data-pipeline to path so imports work
sys.path.insert(0, str(Path(__file__).parent / 'data-pipeline'))

# Now it's safe to import and run the sync
try:
    from sync_complete_final import CompleteProductionSync
    from sync_ultimate import SyncConfig
    
    # Create configuration and run sync
    config = SyncConfig.from_env()
    sync = CompleteProductionSync(config)
    
    print("\nStarting synchronization...")
    print("=" * 60)
    
    # Run the synchronization
    results = sync.sync_all_tables()
    
    # Generate and display report
    report = sync.generate_sync_report(results)
    print(report)
    
except ImportError as e:
    print(f"ERROR: Failed to import sync modules: {e}")
    print("Make sure you're in the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"ERROR during synchronization: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
