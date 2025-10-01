#!/usr/bin/env python3
# data-pipeline/sync_final.py
# Final synchronization script with comprehensive character handling

import os
import sys
import unicodedata
from typing import List, Dict, Tuple
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from airtable_sync import AirTableClient, SyncConfig, PostgreSQLSync, SyncOrchestrator
from airtable_sync_fixed import *

class FinalAirTableClient(AirTableClient):
    """
    Final version of the AirTable client that handles Vietnamese characters
    consistently with how our DDL generation handled them.
    
    The key insight here is that we need to match the sanitization logic
    that was used when creating the database schema. The DDL generation
    removed non-ASCII characters entirely, so we need to do the same
    during synchronization to ensure the names match.
    """
    
    def _sanitize_column_name(self, name: str) -> str:
        """
        Sanitizes column names to match what exists in PostgreSQL.
        
        This version removes non-ASCII characters to match how the DDL
        was generated. Vietnamese characters like đ, ă, ơ, etc. are
        removed rather than preserved. This ensures consistency between
        schema generation and data synchronization.
        
        The process works as follows:
        1. Convert to lowercase for consistency
        2. Replace spaces and special punctuation with underscores
        3. Remove all non-ASCII characters
        4. Clean up any resulting issues (multiple underscores, etc.)
        """
        # Start with basic transformations
        safe = name.lower()
        
        # Replace common separators with underscores
        safe = safe.replace(' ', '_')
        safe = safe.replace('-', '_')
        safe = safe.replace('/', '_')
        safe = safe.replace('.', '_')
        
        # Replace parentheses and brackets
        safe = safe.replace('(', '_')
        safe = safe.replace(')', '_')
        safe = safe.replace('[', '_')
        safe = safe.replace(']', '_')
        
        # Handle percentage signs
        safe = safe.replace('%', 'pct')
        
        # Remove non-ASCII characters completely
        # This is the critical step that matches our DDL generation
        safe = ''.join(char for char in safe if ord(char) < 128)
        
        # Clean up the result
        # Remove any remaining special characters
        safe = ''.join(c if c.isalnum() or c == '_' else '' for c in safe)
        
        # Replace multiple underscores with single underscore
        while '__' in safe:
            safe = safe.replace('__', '_')
        
        # Remove leading/trailing underscores
        safe = safe.strip('_')
        
        # Ensure we don't have an empty string
        if not safe:
            safe = 'field'
            
        return safe

class FinalPostgreSQLSync(PostgreSQLSync):
    """
    Final PostgreSQL sync with both character handling and explicit mappings.
    
    This combines our learning about character encoding with explicit
    mappings for cases where even our improved sanitization doesn't
    match what's in the database.
    """
    
    def __init__(self, config: SyncConfig):
        super().__init__(config)
        
        # Keep our known mappings for special cases
        # These handle situations where the DDL generation created
        # something different than even our corrected sanitization
        self.column_mappings = {
            'contracts_hp_ng': {
                'total_price_incl_transport': 'total_price_incl__transport'
            },
            'contracts_hp_ng___2': {
                'total_price_with_vc': 'total_price_with_vc',
                'imported_quantity_n': 'imported_quantity_n'
            }
        }
    
    def map_column_name(self, table_name: str, column_name: str) -> str:
        """
        Apply any explicit mappings after sanitization.
        
        This two-stage approach gives us the best of both worlds:
        1. Consistent sanitization handles most cases automatically
        2. Explicit mappings handle the exceptions
        """
        if table_name in self.column_mappings:
            return self.column_mappings[table_name].get(column_name, column_name)
        return column_name
    
    def upsert_records(self, table_name: str, records: List[Dict]) -> Tuple[int, int]:
        """
        Upsert with mapping support.
        """
        if not records:
            return 0, 0
        
        # Apply column mappings
        mapped_records = []
        for record in records:
            mapped_record = {}
            for column, value in record.items():
                mapped_column = self.map_column_name(table_name, column)
                mapped_record[mapped_column] = value
            mapped_records.append(mapped_record)
        
        conn = self.get_connection()
        inserted = 0
        updated = 0
        
        try:
            with conn.cursor() as cursor:
                for record in mapped_records:
                    columns = list(record.keys())
                    columns.append('sync_status')
                    columns.append('updated_at')
                    
                    values = list(record.values())
                    values.append('synced')
                    values.append(datetime.now())
                    
                    placeholders = ','.join(['%s'] * len(values))
                    columns_str = ','.join(columns)
                    
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

class FinalSyncOrchestrator(SyncOrchestrator):
    """
    Final orchestrator using our corrected components.
    """
    def __init__(self, config: SyncConfig):
        self.config = config
        self.airtable = FinalAirTableClient(config)
        self.postgres = FinalPostgreSQLSync(config)

def main():
    """
    Main entry point for the final synchronization.
    
    This version incorporates all our learnings:
    1. Complex field type handling (attachments, formulas)
    2. Vietnamese character handling (removing non-ASCII)
    3. Explicit mappings for special cases
    4. Incremental sync support
    """
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    config = SyncConfig.from_env()
    
    if not config.airtable_api_key:
        logger.error("AIRTABLE_API_KEY environment variable not set")
        sys.exit(1)
    
    orchestrator = FinalSyncOrchestrator(config)
    
    logger.info("Starting AirTable to PostgreSQL synchronization (final version)")
    logger.info("This version handles Vietnamese characters and complex field types")
    
    results = orchestrator.sync_all_tables()
    
    report = orchestrator.generate_sync_report(results)
    print("\n" + "="*60)
    print(report)
    
    with open('sync_report.txt', 'w') as f:
        f.write(report)
    
    # Provide summary statistics
    successful_tables = [r for r in results if r['status'] == 'success']
    failed_tables = [r for r in results if r['status'] == 'failed']
    
    if failed_tables:
        print("\nSynchronization completed with errors.")
        print(f"Failed tables: {', '.join([r['table'] for r in failed_tables])}")
        sys.exit(1)
    else:
        print(f"\nSynchronization completed successfully!")
        print(f"Tables synchronized: {len(successful_tables)}")
        total_records = sum(r.get('records_processed', 0) for r in successful_tables)
        print(f"Total records processed: {total_records}")
        sys.exit(0)

if __name__ == "__main__":
    main()
