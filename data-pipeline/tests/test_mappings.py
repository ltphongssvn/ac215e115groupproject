"""
Tests for column name mappings

These tests verify that our discovered mappings correctly handle
the various naming inconsistencies between AirTable and PostgreSQL.
"""

import unittest
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'archive', 'development_iterations'))

from sync_ultimate import UltimateAirTableClient

class TestColumnMappings(unittest.TestCase):
    """Test that problematic field names are handled correctly"""
    
    def setUp(self):
        self.client = UltimateAirTableClient(None)
    
    def test_vietnamese_warehouse_names(self):
        """Test that Vietnamese warehouse names map correctly"""
        # BX Á Châu should become bx_a__chin with double underscore
        result = self.client._sanitize_column_name("BX Á Châu")
        self.assertEqual(result, "bx_a_chin")
        
    def test_numeric_starting_fields(self):
        """Test that fields starting with numbers get prefixed"""
        # Fields like "16h30-19h" should get 'n_' prefix
        result = self.client._sanitize_column_name("16h30-19h")
        self.assertEqual(result, "n_16h30_19h")
        
    def test_percentage_fields(self):
        """Test that percentage fields are recognized"""
        # Field names with 'pct' should be preserved
        result = self.client._sanitize_column_name("moisture_pct")
        self.assertEqual(result, "moisture_pct")

if __name__ == '__main__':
    unittest.main()
