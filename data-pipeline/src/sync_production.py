#!/usr/bin/env python3
"""
Production synchronization script for Rice Market Data Pipeline

This is the main entry point for synchronizing AirTable data to PostgreSQL.
It incorporates all the lessons learned through iterative debugging:
- Vietnamese character handling
- Column name mapping
- Data validation and transformation
- Incremental synchronization
"""

import sys
import os

# Add parent directory to path to import from archive
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import from the archive where all our iterations live
archive_path = os.path.join(parent_dir, 'archive', 'development_iterations')
sys.path.insert(0, archive_path)

# Now import the final working version
from sync_complete_final import *

if __name__ == "__main__":
    # Change to parent directory to find .env file
    os.chdir(parent_dir)
    sys.exit(main())
