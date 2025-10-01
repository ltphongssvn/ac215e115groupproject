#!/usr/bin/env python3
# data-pipeline/airtable_sync.py
# Main synchronization orchestrator for AirTable to PostgreSQL data pipeline
# This script coordinates the entire sync process, handling errors and maintaining state

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import requests
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
import time
from dataclasses import dataclass, asdict
import hashlib

# Configure logging with detailed formatting for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SyncConfig:
    """
    Configuration for the synchronization process.
    
    This dataclass centralizes all configuration in one place, making it easy
    to adjust settings without diving into the code. Think of this as the 
    control panel for your synchronization system - all the knobs and switches
    are here.
    """
    # AirTable configuration
    airtable_base_id: str
    airtable_api_key: str
    airtable_api_url: str = "https://api.airtable.com/v0"
    
    # PostgreSQL configuration  
    postgres_host: str = "localhost"
    postgres_port: int = 5433  # Using 5433 since 5432 is occupied
    postgres_database: str = "rice_market_db"
    postgres_user: str = "rice_admin"
    postgres_password: str = "localdev123"
    postgres_schema: str = "airtable_sync"
    
    # Sync behavior configuration
    batch_size: int = 100  # Records to process at once
    rate_limit_delay: float = 0.2  # Seconds between AirTable API calls (5 req/sec limit)
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Sync strategy
    sync_mode: str = "incremental"  # "full" or "incremental"
    track_changes: bool = True
    
    @classmethod
    def from_env(cls) -> 'SyncConfig':
        """
        Creates configuration from environment variables.
        
        This pattern allows you to keep sensitive information like API keys
        out of your code. In production, these would come from secure secret
        management systems like Google Secret Manager.
        """
        return cls(
            airtable_base_id=os.getenv('AIRTABLE_BASE_ID', 'appmeTyHLozoqighD'),
            airtable_api_key=os.getenv('AIRTABLE_API_KEY', ''),
            postgres_password=os.getenv('POSTGRES_PASSWORD', 'localdev123')
        )


class AirTableClient:
    """
    Handles all interactions with the AirTable API.
    
    This class encapsulates the complexity of working with AirTable's API,
    including rate limiting, pagination, and error handling. It's like having
    a skilled interpreter who knows how to communicate with AirTable effectively
    and politely (respecting rate limits).
    """
    
    def __init__(self, config: SyncConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.airtable_api_key}',
            'Content-Type': 'application/json'
        })
        
        # Table ID mappings discovered from our documentation parsing
        self.table_ids = {
            'contracts_hp_ng': 'tbl7sHbwOCOTjL2MC',
            'contracts_hp_ng___2': 'tbllz4cazITSwnXIo', 
            'customers': 'tblDUfIlNy07Z0hiL',
            'shipments': 'tblSj7JcxYYfs6Dcl',
            'inventory_movements': 'tblhb3Vxhi6Yt0BDw',
            'finished_goods': 'tblNY26FnHswHRcWS',
            'commodities': 'tblawXefYSXa6UFSX',
            'price_lists': 'tbl0B7ON9dDTtj3mP'
        }
        
    def fetch_table_records(self, table_name: str, 
                           modified_since: Optional[datetime] = None) -> List[Dict]:
        """
        Fetches all records from a specific AirTable table.
        
        This method handles AirTable's pagination automatically. AirTable returns
        at most 100 records per request, so we need to make multiple requests
        for tables with more data. The 'offset' parameter in the response tells
        us if there are more records to fetch.
        
        The modified_since parameter enables incremental sync - we only fetch
        records that changed since our last sync, dramatically reducing data
        transfer and processing time.
        """
        if table_name not in self.table_ids:
            raise ValueError(f"Unknown table: {table_name}")
            
        table_id = self.table_ids[table_name]
        url = f"{self.config.airtable_api_url}/{self.config.airtable_base_id}/{table_id}"
        
        all_records = []
        offset = None
        
        # Build filter formula for incremental sync
        params = {'pageSize': 100}
        if modified_since:
            # AirTable's formula syntax for date comparison
            formula = f"IS_AFTER(LAST_MODIFIED_TIME(), '{modified_since.isoformat()}')"
            params['filterByFormula'] = formula
            
        while True:
            if offset:
                params['offset'] = offset
                
            # Respect rate limits
            time.sleep(self.config.rate_limit_delay)
            
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                records = data.get('records', [])
                all_records.extend(records)
                
                # Check if there are more pages
                offset = data.get('offset')
                if not offset:
                    break
                    
                logger.info(f"Fetched {len(records)} records from {table_name}, "
                          f"total so far: {len(all_records)}")
                          
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching from {table_name}: {e}")
                raise
                
        logger.info(f"Completed fetching {len(all_records)} total records from {table_name}")
        return all_records
    
    def transform_record(self, record: Dict, table_name: str) -> Dict:
        """
        Transforms an AirTable record into PostgreSQL-compatible format.
        
        This transformation handles several important conversions:
        1. Extracting the record ID for tracking
        2. Converting field names to PostgreSQL-safe column names
        3. Handling relationship fields (which are arrays of record IDs)
        4. Managing data type conversions
        5. Converting Airtable JSON NaN values to PostgreSQL NULL values
        
        The NaN handling is critical for numeric fields where Airtable sends
        {"specialValue": "NaN"} when a calculated field has no valid value.
        """
        transformed = {
            'airtable_record_id': record['id'],
            'last_airtable_modified': record.get('createdTime')
        }
        
        fields = record.get('fields', {})
        
        for field_name, value in fields.items():
            # Convert field name to PostgreSQL column name
            pg_column = self._sanitize_column_name(field_name)
            
            # CRITICAL FIX: Check for Airtable's JSON NaN representation
            if isinstance(value, str) and value.strip() == '{"specialValue": "NaN"}':
                # Convert to None, which PostgreSQL will store as NULL
                transformed[pg_column] = None
                logger.debug(f"Converting JSON NaN to NULL for field: {field_name}")
            
            # Handle relationship fields (arrays of record IDs)
            elif isinstance(value, list) and value and value[0].startswith('rec'):
                # Skip relationship fields - handled separately
                continue
                
            # Pass through basic Python types
            elif isinstance(value, (int, float, str, bool)) or value is None:
                transformed[pg_column] = value
                
            # Complex types get JSON serialization
            else:
                transformed[pg_column] = Json(value)
        
        return transformed
    def _sanitize_column_name(self, name: str) -> str:
        """
        Converts AirTable field names to PostgreSQL column names.
        
        This mirrors the logic we used in our DDL generation - ensuring
        consistency between what we expect in the database and what we're
        inserting.
        """
        safe = name.lower()
        safe = safe.replace(' ', '_')
        safe = safe.replace('(', '')
        safe = safe.replace(')', '')
        safe = safe.replace('%', 'pct')
        safe = safe.replace('/', '_')
        safe = safe.replace('-', '_')
        
        # Remove any remaining special characters
        safe = ''.join(c if c.isalnum() or c == '_' else '' for c in safe)
        
        return safe


class PostgreSQLSync:
    """
    Manages PostgreSQL operations and data persistence.
    
    This class handles the PostgreSQL side of the synchronization, including
    connection pooling for efficiency, transaction management for data integrity,
    and conflict resolution for handling concurrent updates.
    """
    
    def __init__(self, config: SyncConfig):
        self.config = config
        
        # Connection pooling improves performance by reusing database connections
        # instead of creating new ones for each operation
        self.pool = SimpleConnectionPool(
            1, 20,  # Min and max connections
            host=config.postgres_host,
            port=config.postgres_port,
            database=config.postgres_database,
            user=config.postgres_user,
            password=config.postgres_password
        )
        
    def get_connection(self):
        """Gets a connection from the pool."""
        return self.pool.getconn()
    
    def return_connection(self, conn):
        """Returns a connection to the pool for reuse."""
        self.pool.putconn(conn)
        
    def upsert_records(self, table_name: str, records: List[Dict]) -> Tuple[int, int]:
        """
        Performs an UPSERT operation (INSERT or UPDATE) for multiple records.
        
        UPSERT is a critical pattern in data synchronization. When we receive
        a record from AirTable, we don't know if it's new or an update to an
        existing record. UPSERT handles both cases elegantly:
        - If the airtable_record_id doesn't exist, insert a new record
        - If it does exist, update the existing record with new values
        
        PostgreSQL's ON CONFLICT clause makes this atomic, preventing race
        conditions in concurrent scenarios.
        """
        if not records:
            return 0, 0
            
        conn = self.get_connection()
        inserted = 0
        updated = 0
        
        try:
            with conn.cursor() as cursor:
                for record in records:
                    # Build the UPSERT query dynamically based on fields present
                    columns = list(record.keys())
                    columns.append('sync_status')
                    columns.append('updated_at')
                    
                    values = list(record.values())
                    values.append('synced')
                    values.append(datetime.now())
                    
                    # Create placeholders for the SQL query
                    placeholders = ','.join(['%s'] * len(values))
                    columns_str = ','.join(columns)
                    
                    # Build the UPDATE clause for conflicts
                    update_cols = [f"{col} = EXCLUDED.{col}" 
                                 for col in columns 
                                 if col != 'airtable_record_id']
                    update_str = ','.join(update_cols)
                    
                    query = f"""
                    INSERT INTO {self.config.postgres_schema}.{table_name} 
                    ({columns_str})
                    VALUES ({placeholders})
                    ON CONFLICT (airtable_record_id) 
                    DO UPDATE SET {update_str}
                    RETURNING (xmax = 0) AS inserted
                    """
                    
                    cursor.execute(query, values)
                    result = cursor.fetchone()
                    
                    if result and result[0]:
                        inserted += 1
                    else:
                        updated += 1
                        
                conn.commit()
                logger.info(f"Upserted {len(records)} records into {table_name}: "
                          f"{inserted} inserted, {updated} updated")
                          
        except Exception as e:
            conn.rollback()
            logger.error(f"Error upserting records: {e}")
            raise
        finally:
            self.return_connection(conn)
            
        return inserted, updated
    
    def sync_relationships(self, table_name: str, relationships: List[Dict]):
        """
        Synchronizes many-to-many relationships through junction tables.
        
        Relationships in AirTable are bi-directional and stored as arrays of
        record IDs. In PostgreSQL, we represent these with junction tables.
        This method manages those junction table entries, ensuring they stay
        synchronized with AirTable's relationships.
        
        The challenge here is handling deletions - if a relationship is removed
        in AirTable, we need to remove it from our junction table too.
        """
        # This is a complex operation that we'll implement after the basic sync works
        pass
    
    def get_last_sync_time(self, table_name: str) -> Optional[datetime]:
        """
        Retrieves the timestamp of the last successful sync for a table.
        
        This enables incremental synchronization by tracking when each table
        was last updated. We store this in a separate sync_status table to
        maintain a full audit trail of synchronization operations.
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT MAX(updated_at) as last_sync
                    FROM {}.{}
                    WHERE sync_status = 'synced'
                """.format(self.config.postgres_schema, table_name))
                
                result = cursor.fetchone()
                return result['last_sync'] if result and result['last_sync'] else None
                
        finally:
            self.return_connection(conn)


class SyncOrchestrator:
    """
    Orchestrates the complete synchronization process.
    
    This is the conductor of our synchronization symphony, coordinating
    all the different components to work together harmoniously. It handles
    the overall flow, error recovery, and monitoring of the sync process.
    """
    
    def __init__(self, config: SyncConfig):
        self.config = config
        self.airtable = AirTableClient(config)
        self.postgres = PostgreSQLSync(config)
        
    def sync_table(self, table_name: str) -> Dict[str, Any]:
        """
        Synchronizes a single table from AirTable to PostgreSQL.
        
        This method orchestrates the complete sync process for one table:
        1. Determine what needs to be synced (full or incremental)
        2. Fetch data from AirTable
        3. Transform the data for PostgreSQL
        4. Persist to PostgreSQL
        5. Handle relationships
        6. Update sync metadata
        """
        logger.info(f"Starting sync for table: {table_name}")
        start_time = datetime.now()
        
        # Determine sync strategy
        last_sync = None
        if self.config.sync_mode == "incremental":
            last_sync = self.postgres.get_last_sync_time(table_name)
            if last_sync:
                logger.info(f"Performing incremental sync since {last_sync}")
            else:
                logger.info("No previous sync found, performing full sync")
                
        # Fetch records from AirTable
        try:
            records = self.airtable.fetch_table_records(table_name, last_sync)
        except Exception as e:
            logger.error(f"Failed to fetch records from AirTable: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'table': table_name
            }
            
        # Transform records for PostgreSQL
        transformed_records = []
        for record in records:
            transformed = self.airtable.transform_record(record, table_name)
            transformed_records.append(transformed)
            
        # Upsert records to PostgreSQL
        if transformed_records:
            inserted, updated = self.postgres.upsert_records(table_name, transformed_records)
        else:
            inserted = updated = 0
            logger.info(f"No records to sync for {table_name}")
            
        # Calculate sync metrics
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            'status': 'success',
            'table': table_name,
            'records_processed': len(records),
            'inserted': inserted,
            'updated': updated,
            'duration_seconds': duration,
            'timestamp': datetime.now().isoformat()
        }
    
    def sync_all_tables(self) -> List[Dict]:
        """
        Synchronizes all tables in the correct order.
        
        Order matters because of foreign key constraints. We sync tables
        that others depend on first (like customers and commodities),
        then tables with foreign keys, and finally junction tables.
        """
        # Define sync order based on dependencies
        sync_order = [
            'customers',      # No dependencies
            'commodities',    # No dependencies  
            'price_lists',    # Depends on commodities
            'contracts_hp_ng',  # Depends on customers, commodities
            'contracts_hp_ng___2',  # Depends on customers, commodities
            'shipments',      # Depends on customers, contracts, commodities
            'inventory_movements',  # Depends on multiple tables
            'finished_goods'  # Depends on customers, commodities
        ]
        
        results = []
        for table_name in sync_order:
            result = self.sync_table(table_name)
            results.append(result)
            
            # Stop if a table fails to sync
            if result['status'] == 'failed':
                logger.error(f"Stopping sync due to failure in {table_name}")
                break
                
        return results
    
    def generate_sync_report(self, results: List[Dict]) -> str:
        """
        Generates a human-readable report of the sync operation.
        
        This report helps you understand what happened during synchronization,
        making it easier to monitor and debug the process.
        """
        report = []
        report.append("="*60)
        report.append("SYNCHRONIZATION REPORT")
        report.append("="*60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        total_records = 0
        total_inserted = 0
        total_updated = 0
        total_duration = 0
        
        for result in results:
            report.append(f"Table: {result['table']}")
            report.append(f"  Status: {result['status']}")
            
            if result['status'] == 'success':
                report.append(f"  Records Processed: {result['records_processed']}")
                report.append(f"  Inserted: {result['inserted']}")
                report.append(f"  Updated: {result['updated']}")
                report.append(f"  Duration: {result['duration_seconds']:.2f} seconds")
                
                total_records += result['records_processed']
                total_inserted += result['inserted']
                total_updated += result['updated']
                total_duration += result['duration_seconds']
            else:
                report.append(f"  Error: {result.get('error', 'Unknown error')}")
                
            report.append("")
            
        report.append("="*60)
        report.append("SUMMARY")
        report.append(f"Total Records Processed: {total_records}")
        report.append(f"Total Inserted: {total_inserted}")
        report.append(f"Total Updated: {total_updated}")
        report.append(f"Total Duration: {total_duration:.2f} seconds")
        report.append("="*60)
        
        return "\n".join(report)


def main():
    """
    Main entry point for the synchronization script.
    
    This function sets up the configuration, creates the orchestrator,
    and runs the synchronization process.
    """
    # Load configuration from environment
    config = SyncConfig.from_env()
    
    # Validate configuration
    if not config.airtable_api_key:
        logger.error("AIRTABLE_API_KEY environment variable not set")
        sys.exit(1)
        
    # Create orchestrator and run sync
    orchestrator = SyncOrchestrator(config)
    
    logger.info("Starting AirTable to PostgreSQL synchronization")
    results = orchestrator.sync_all_tables()
    
    # Generate and display report
    report = orchestrator.generate_sync_report(results)
    print(report)
    
    # Write report to file
    with open('sync_report.txt', 'w') as f:
        f.write(report)
        
    # Exit with appropriate code
    if any(r['status'] == 'failed' for r in results):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
