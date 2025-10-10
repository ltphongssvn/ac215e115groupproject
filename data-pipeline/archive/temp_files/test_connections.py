#!/usr/bin/env python3
# data-pipeline/test_connections.py
# Tests connections to both AirTable and PostgreSQL before running full sync

import os
import sys
from dotenv import load_dotenv
import requests
import psycopg2
import json

# Load environment variables from .env file
load_dotenv('data-pipeline/.env')

def test_airtable_connection():
    """
    Tests the AirTable API connection by attempting to fetch basic information
    about the base. This verifies that our API key works and has the necessary
    permissions to read data from the base.
    """
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    
    if not api_key:
        print("ERROR: AIRTABLE_API_KEY not found in environment")
        return False
    
    # Test with a simple API call to list tables (using one we know exists)
    url = f"https://api.airtable.com/v0/{base_id}/tblDUfIlNy07Z0hiL"  # Customers table
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, params={'maxRecords': 1})
        
        if response.status_code == 200:
            data = response.json()
            print("✓ AirTable connection successful")
            print(f"  Base ID: {base_id}")
            print(f"  Can read data: Yes")
            if data.get('records'):
                print(f"  Sample record ID: {data['records'][0]['id']}")
            return True
        elif response.status_code == 401:
            print("✗ AirTable authentication failed - check your API key")
            return False
        elif response.status_code == 403:
            print("✗ AirTable permission denied - your token may lack necessary scopes")
            return False
        else:
            print(f"✗ AirTable connection failed with status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ AirTable connection error: {e}")
        return False

def test_postgresql_connection():
    """
    Tests the PostgreSQL connection by attempting to connect to the database
    and verify that our schema and tables exist. This ensures the Docker
    container is running and accessible.
    """
    try:
        # Build connection string from environment variables
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', '5433')),
            database=os.getenv('POSTGRES_DATABASE', 'rice_market_db'),
            user=os.getenv('POSTGRES_USER', 'rice_admin'),
            password=os.getenv('POSTGRES_PASSWORD', 'localdev123')
        )
        
        with conn.cursor() as cursor:
            # Check if our schema exists
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = 'airtable_sync'
                )
            """)
            schema_exists = cursor.fetchone()[0]
            
            # Count tables in our schema
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'airtable_sync'
                AND table_type = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()[0]
            
            print("✓ PostgreSQL connection successful")
            print(f"  Host: {os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}")
            print(f"  Database: {os.getenv('POSTGRES_DATABASE')}")
            print(f"  Schema exists: {'Yes' if schema_exists else 'No'}")
            print(f"  Tables found: {table_count}")
            
            # Show a few table names as confirmation
            if table_count > 0:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'airtable_sync'
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    LIMIT 5
                """)
                tables = cursor.fetchall()
                print(f"  Sample tables: {', '.join([t[0] for t in tables])}")
            
            return schema_exists and table_count > 0
            
    except psycopg2.OperationalError as e:
        print(f"✗ PostgreSQL connection failed")
        print(f"  Error: {e}")
        print(f"  Make sure Docker containers are running: docker compose ps")
        return False
    except Exception as e:
        print(f"✗ PostgreSQL error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """
    Main test function that verifies both connections and provides guidance
    on next steps based on the results.
    """
    print("Testing Data Pipeline Connections")
    print("="*50)
    
    airtable_ok = test_airtable_connection()
    print()
    postgres_ok = test_postgresql_connection()
    
    print("\n" + "="*50)
    if airtable_ok and postgres_ok:
        print("✓ All connections successful!")
        print("\nYou can now run the synchronization:")
        print("  cd data-pipeline")
        print("  python airtable_sync.py")
    else:
        print("✗ Connection issues detected")
        if not postgres_ok:
            print("\nTo fix PostgreSQL:")
            print("  1. Check if Docker is running: docker compose ps")
            print("  2. If not running: docker compose up -d")
            print("  3. Check logs: docker logs rice_market_postgres")
        if not airtable_ok:
            print("\nTo fix AirTable:")
            print("  1. Verify your API key is correct")
            print("  2. Check that the key has access to the base")
            print("  3. Ensure the base ID is correct")
    
    return 0 if (airtable_ok and postgres_ok) else 1

if __name__ == "__main__":
    sys.exit(main())
