#!/usr/bin/env python3
"""
Core synchronization module for Rice Market Data Pipeline
This module contains the essential synchronization logic developed through
iterative debugging with production data.
"""

# Import the actual implementation from archive
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'archive', 'development_iterations'))

from airtable_sync import *

# Re-export the main classes for cleaner imports
__all__ = ['SyncConfig', 'AirTableClient', 'PostgreSQLSync', 'SyncOrchestrator']
