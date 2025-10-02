#!/usr/bin/env python3
# data-pipeline/diagnose_airtable_data.py
# Diagnoses the structure of AirTable data to understand the dictionary issue

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('data-pipeline/.env')

def fetch_sample_record(base_id, table_id, api_key):
    """Fetches a single record to examine its structure."""
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {'maxRecords': 1}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        return None
    
    data = response.json()
    records = data.get('records', [])
    return records[0] if records else None

def analyze_record_structure(record):
    """Analyzes the structure of a record to identify complex fields."""
    if not record:
        return
    
    print("Record Structure Analysis:")
    print("=" * 60)
    print(f"Record ID: {record.get('id')}")
    print(f"Created Time: {record.get('createdTime')}")
    print("\nField Analysis:")
    print("-" * 40)
    
    fields = record.get('fields', {})
    for field_name, field_value in fields.items():
        value_type = type(field_value).__name__
        print(f"\nField: {field_name}")
        print(f"  Type: {value_type}")
        
        if isinstance(field_value, dict):
            print("  >>> This is a DICTIONARY - needs special handling!")
            print(f"  Structure: {json.dumps(field_value, indent=4, default=str)[:200]}")
        elif isinstance(field_value, list):
            print(f"  >>> This is a LIST with {len(field_value)} items")
            if field_value and isinstance(field_value[0], dict):
                print("  >>> Contains dictionaries - likely linked records!")
                print(f"  First item: {json.dumps(field_value[0], indent=4, default=str)[:200]}")
            elif field_value:
                print(f"  First item type: {type(field_value[0]).__name__}")
                print(f"  First item value: {field_value[0]}")
        else:
            # Simple value - truncate if too long
            value_str = str(field_value)
            if len(value_str) > 50:
                value_str = value_str[:50] + "..."
            print(f"  Value: {value_str}")

if __name__ == "__main__":
    print("AirTable Data Structure Diagnostic")
    print("=" * 60)
    
    # Load configuration
    airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
    airtable_api_key = os.getenv('AIRTABLE_API_KEY')
    
    if not airtable_base_id or not airtable_api_key:
        print("ERROR: Missing environment variables")
        sys.exit(1)
    
    # Test with customers table first (since that's where the error occurred)
    table_id = 'tblDUfIlNy07Z0hiL'  # customers table
    
    print(f"Fetching sample record from customers table...")
    print("-" * 60)
    
    record = fetch_sample_record(airtable_base_id, table_id, airtable_api_key)
    
    if record:
        analyze_record_structure(record)
        
        print("\n" + "=" * 60)
        print("Diagnosis Complete")
        print("\nThe fields marked with '>>>' need special handling in the sync code.")
        print("Dictionary and list fields typically represent:")
        print("  - Linked records (relationships to other tables)")
        print("  - Multiple values (like tags or categories)")
        print("  - Attachments or complex metadata")
        print("\nThese need to be converted to simple values or handled separately.")
    else:
        print("No records found or error fetching data")

