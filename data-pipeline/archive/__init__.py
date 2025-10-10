"""
Rice Market Data Pipeline Module

This module handles synchronization between AirTable and PostgreSQL.
It's designed to work as part of the larger ac215e115groupproject.
"""

from .src.sync_production import main as sync_data

__version__ = "1.0.0"
__all__ = ["sync_data"]
