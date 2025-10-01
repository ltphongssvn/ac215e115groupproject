#!/usr/bin/env python3
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/test_nan_fix.py
# Test script to verify that JSON NaN values are properly converted to NULL

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the fixed AirTableClient class
from airtable_sync import AirTableClient, SyncConfig

# Create a test function that simulates what happens during sync
def test_nan_transformation():
    """
    Tests whether the transform_record method properly handles JSON NaN values.
    We'll create a mock Airtable record with a NaN value and verify it converts to None.
    """
    print("Testing JSON NaN to NULL conversion...")
    print("="*50)
    
    # Create a minimal config for testing
    config = SyncConfig.from_env()
    client = AirTableClient(config)
    
    # Create a mock Airtable record that simulates what we receive from the API
    # This mimics a commodity with no valid average price
    mock_record = {
        'id': 'recTEST123',
        'createdTime': '2024-01-01T00:00:00Z',
        'fields': {
            'Commodity Name': 'TEST COMMODITY',
            'Total Contracted Quantity (kg)': '0',
            'Average Unit Price from Contracts': '{"specialValue": "NaN"}',  # The problematic value
            'Some Other Field': 'Regular text value'
        }
    }
    
    # Transform the record using our fixed method
    print("Input record fields:")
    for field, value in mock_record['fields'].items():
        print(f"  {field}: {value}")
    
    print("\nApplying transformation...")
    transformed = client.transform_record(mock_record, 'commodities')
    
    print("\nTransformed record:")
    for field, value in transformed.items():
        if field != 'airtable_record_id' and field != 'last_airtable_modified':
            print(f"  {field}: {value} (type: {type(value).__name__})")
    
    # Check if the NaN was converted to None
    price_field = 'average_unit_price_from_contracts'
    if price_field in transformed:
        if transformed[price_field] is None:
            print("\n✓ SUCCESS: JSON NaN was converted to None (will be NULL in PostgreSQL)")
            return True
        else:
            print(f"\n✗ FAILURE: JSON NaN was not converted. Value is: {transformed[price_field]}")
            return False
    else:
        print(f"\n✗ ERROR: Field {price_field} not found in transformed record")
        return False

if __name__ == "__main__":
    try:
        success = test_nan_transformation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
