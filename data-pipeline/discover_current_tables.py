#!/usr/bin/env python3
# data-pipeline/discover_current_tables.py
# Discovers what tables actually exist in the current AirTable base

import os
import requests
from dotenv import load_dotenv

load_dotenv('.env')

def discover_tables():
    """
    Uses the AirTable Meta API to discover all tables in the base.
    This will show us the actual table IDs that exist in your base.
    """
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    
    # The Meta API endpoint tells us about the structure of a base
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"Discovering tables in base: {base_id}")
    print("="*50)
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            tables = data.get('tables', [])
            
            print(f"Found {len(tables)} tables:\n")
            for table in tables:
                print(f"Table Name: {table['name']}")
                print(f"  ID: {table['id']}")
                print(f"  Fields: {len(table.get('fields', []))}")
                print()
                
            # Save the table IDs for future reference
            table_map = {t['name']: t['id'] for t in tables}
            print("\nTable ID Mapping for your code:")
            print("-"*50)
            print("table_ids = {")
            for name, tid in table_map.items():
                print(f"    '{name}': '{tid}',")
            print("}")
            
        elif response.status_code == 403:
            print("Permission denied. Your API token might not have the")
            print("'schema.bases:read' scope needed for the Meta API.")
            print("\nTrying alternative method...")
            
            # If Meta API fails, try to fetch from known table names
            # These are common table names in your rice market system
            test_tables = ['Commodities', 'Customers', 'Contracts', 'Shipments']
            
            for table_name in test_tables:
                # Try the table name as-is in the URL
                test_url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
                test_response = requests.get(test_url, headers=headers, 
                                            params={'maxRecords': 1})
                
                if test_response.status_code == 200:
                    print(f"✓ Found table by name: {table_name}")
                    # The response includes the records but not the table ID directly
                    # We'd need to parse the response to find the actual ID
                elif test_response.status_code == 404:
                    print(f"✗ Table '{table_name}' not found")
        
        else:
            print(f"Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error discovering tables: {e}")

if __name__ == "__main__":
    discover_tables()
