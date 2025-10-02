#!/usr/bin/env python3
# data-pipeline/sync_orchestrator.py
# Orchestrates the synchronization by calling the granular methods

import os
import sys
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv('data-pipeline/.env')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_ultimate import *

# AirTable configuration - table names and their IDs
AIRTABLE_TABLES = {
    'customers': 'tblDUfIlNy07Z0hiL',
    'commodities': 'tblawXefYSXa6UFSX',
    'contracts_hp_ng': 'tbl7sHbwOCOTjL2MC',
    'contracts_hp_ng___2': 'tbllz4cazITSwnXIo',
    'shipments': 'tblSj7JcxYYfs6Dcl',
    'inventory_movements': 'tblhb3Vxhi6Yt0BDw',
    'finished_goods': 'tblNY26FnHswHRcWS',
    'price_lists': 'tbl0B7ON9dDTtj3mP'
}

def fetch_airtable_data(base_id, table_id, api_key):
    """
    Fetches all records from an AirTable table.
    Handles pagination if there are more than 100 records.
    """
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    headers = {'Authorization': f'Bearer {api_key}'}
    
    all_records = []
    offset = None
    
    while True:
        params = {}
        if offset:
            params['offset'] = offset
            
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"  ERROR fetching data: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            break
            
        data = response.json()
        all_records.extend(data.get('records', []))
        
        # Check if there are more pages
        offset = data.get('offset')
        if not offset:
            break
            
    return all_records

if __name__ == "__main__":
    print("AirTable to PostgreSQL Synchronization Orchestrator")
    print("=" * 70)
    
    # Load configuration
    airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
    airtable_api_key = os.getenv('AIRTABLE_API_KEY')
    
    if not airtable_base_id or not airtable_api_key:
        print("ERROR: Missing required environment variables")
        sys.exit(1)
    
    print(f"Using AirTable Base: {airtable_base_id}")
    print(f"Starting synchronization at {datetime.now()}")
    print("-" * 70)
    
    try:
        # Create configuration and sync object
        config = SyncConfig(
            airtable_base_id=airtable_base_id,
            airtable_api_key=airtable_api_key
        )
        
        sync = UltimateProductionPostgreSQLSync(config)
        print("Sync object initialized successfully\n")
        
        total_inserted = 0
        total_updated = 0
        
        # Synchronize each table
        for table_name, table_id in AIRTABLE_TABLES.items():
            print(f"Synchronizing table: {table_name}")
            print(f"  AirTable ID: {table_id}")
            
            # Check last sync time
            last_sync = sync.get_last_sync_time(table_name)
            if last_sync:
                print(f"  Last synchronized: {last_sync}")
            
            # Fetch data from AirTable
            print(f"  Fetching records from AirTable...")
            records = fetch_airtable_data(airtable_base_id, table_id, airtable_api_key)
            print(f"  Found {len(records)} records")
            
            if records:
                # Sync the records
                print(f"  Upserting records to PostgreSQL...")
                inserted, updated = sync.upsert_records(table_name, records)
                print(f"  Result: {inserted} inserted, {updated} updated")
                
                total_inserted += inserted
                total_updated += updated
                
                # Sync relationships if the table has any
                # The sync object should handle this internally based on the table
                print(f"  Synchronizing relationships...")
                sync.sync_relationships(table_name, records)
                print(f"  Relationships synchronized")
            
            print()  # Empty line between tables
        
        print("-" * 70)
        print(f"Synchronization complete at {datetime.now()}")
        print(f"Total records: {total_inserted} inserted, {total_updated} updated")
        
    except Exception as e:
        print(f"\nERROR during synchronization: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 70)
