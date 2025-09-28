#!/usr/bin/env python3
# data-pipeline/sync_with_mappings.py
# Enhanced sync script with column name mapping to handle schema inconsistencies

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from airtable_sync_fixed import *

class MappedPostgreSQLSync(PostgreSQLSync):
    """
    PostgreSQL sync class with column name mapping capabilities.
    
    This class understands that sometimes the column names in PostgreSQL
    don't exactly match what our sanitization function produces. Rather
    than trying to make everything perfect, we maintain explicit mappings
    for the exceptions. This approach is more maintainable than complex
    regex rules that try to handle every edge case.
    """
    
    def __init__(self, config: SyncConfig):
        super().__init__(config)
        
        # Define column name mappings for known discrepancies
        # Format: {table_name: {generated_name: actual_db_name}}
        self.column_mappings = {
            'contracts_hp_ng': {
                'total_price_incl_transport': 'total_price_incl__transport'
            },
            'contracts_hp_ng___2': {
                'total_price_incl_transport': 'total_price_incl__transport',
                'imported_quantity_n': 'imported_quantity_n'  # Might need this too
            }
        }
    
    def map_column_name(self, table_name: str, column_name: str) -> str:
        """
        Maps a column name to its actual database column name if a mapping exists.
        
        This method checks if we have a specific mapping for this table and column
        combination. If we do, it returns the mapped name. Otherwise, it returns
        the original name. This allows us to handle exceptions without changing
        the general case.
        """
        if table_name in self.column_mappings:
            return self.column_mappings[table_name].get(column_name, column_name)
        return column_name
    
    def upsert_records(self, table_name: str, records: List[Dict]) -> Tuple[int, int]:
        """
        Enhanced upsert that applies column name mappings before inserting.
        
        This version processes each record to apply any necessary column name
        mappings before attempting the database insert. This ensures that the
        column names we use match what actually exists in the database.
        """
        if not records:
            return 0, 0
        
        # Apply column mappings to all records
        mapped_records = []
        for record in records:
            mapped_record = {}
            for column, value in record.items():
                # Apply mapping if one exists, otherwise use original name
                mapped_column = self.map_column_name(table_name, column)
                mapped_record[mapped_column] = value
            mapped_records.append(mapped_record)
        
        # Now call the parent upsert with the mapped records
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

class MappedSyncOrchestrator(FixedSyncOrchestrator):
    """
    Orchestrator that uses our mapped PostgreSQL sync class.
    """
    def __init__(self, config: SyncConfig):
        self.config = config
        self.airtable = FixedAirTableClient(config)
        self.postgres = MappedPostgreSQLSync(config)  # Use our mapped version

def main():
    """
    Main entry point with column name mapping support.
    """
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    config = SyncConfig.from_env()
    
    if not config.airtable_api_key:
        logger.error("AIRTABLE_API_KEY environment variable not set")
        sys.exit(1)
    
    orchestrator = MappedSyncOrchestrator(config)
    
    logger.info("Starting AirTable to PostgreSQL synchronization (with column mappings)")
    results = orchestrator.sync_all_tables()
    
    report = orchestrator.generate_sync_report(results)
    print(report)
    
    with open('sync_report.txt', 'w') as f:
        f.write(report)
    
    if any(r['status'] == 'failed' for r in results):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
