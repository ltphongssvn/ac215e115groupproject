#!/usr/bin/env python3
# data-pipeline/discover_mappings.py
# Discover all column name mismatches between AirTable and PostgreSQL

import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_ultimate import *

def discover_all_mappings(config: SyncConfig):
    """
    Discovers all column name mappings needed between AirTable and PostgreSQL.
    
    This function fetches a sample record from each AirTable table, transforms
    the field names using our sanitization logic, then compares with what
    actually exists in PostgreSQL to identify all mismatches.
    """
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    airtable = UltimateAirTableClient(config)
    postgres = UltimateProductionPostgreSQLSync(config)
    
    all_mappings = {}
    
    tables = ['customers', 'commodities', 'price_lists', 'contracts_hp_ng',
              'contracts_hp_ng___2', 'shipments', 'inventory_movements', 'finished_goods']
    
    for table_name in tables:
        print(f"\nAnalyzing {table_name}...")
        
        # Get actual PostgreSQL columns
        conn = postgres.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s
                    AND column_name NOT IN ('id', 'created_at', 'updated_at', 
                                           'sync_status', 'last_airtable_modified', 
                                           'airtable_record_id')
                """, (config.postgres_schema, table_name))
                
                pg_columns = {row[0] for row in cursor.fetchall()}
                
        finally:
            postgres.return_connection(conn)
        
        # Fetch sample records from AirTable to see what fields exist
        try:
            records = airtable.fetch_table_records(table_name)[:1]  # Just get one record
            if records:
                sample_record = airtable.transform_record(records[0], table_name)
                airtable_columns = set(sample_record.keys()) - {'airtable_record_id', 'last_airtable_modified'}
                
                # Find mismatches
                mismatches = {}
                for at_col in airtable_columns:
                    if at_col not in pg_columns:
                        # Try to find the best match
                        possible_matches = []
                        for pg_col in pg_columns:
                            # Check if they're similar (ignoring underscores)
                            if at_col.replace('_', '') == pg_col.replace('_', ''):
                                possible_matches.append(pg_col)
                        
                        if len(possible_matches) == 1:
                            mismatches[at_col] = possible_matches[0]
                            print(f"  Mapping needed: '{at_col}' -> '{possible_matches[0]}'")
                        elif len(possible_matches) > 1:
                            print(f"  Multiple possible matches for '{at_col}': {possible_matches}")
                        else:
                            print(f"  No match found for '{at_col}'")
                
                if mismatches:
                    all_mappings[table_name] = mismatches
                    
        except Exception as e:
            print(f"  Error analyzing table: {e}")
    
    # Generate Python code for the mappings
    print("\n\n" + "="*70)
    print("COMPLETE MAPPING DICTIONARY:")
    print("="*70)
    print("column_mappings = {")
    for table, mappings in all_mappings.items():
        print(f"    '{table}': {{")
        for src, dst in mappings.items():
            print(f"        '{src}': '{dst}',")
        print("    },")
    print("}")
    
    # Save to JSON file
    with open('discovered_mappings.json', 'w') as f:
        json.dump(all_mappings, f, indent=2)
    print("\nMappings saved to discovered_mappings.json")

if __name__ == "__main__":
    config = SyncConfig.from_env()
    discover_all_mappings(config)
