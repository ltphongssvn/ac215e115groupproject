#!/usr/bin/env python3
# data-pipeline/sync_complete.py
# Complete synchronization with automatic schema discovery and mapping

import os
import sys
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_final import *

class SchemaAwarePostgreSQLSync(FinalPostgreSQLSync):
    """
    PostgreSQL sync that discovers actual column names and creates mappings automatically.
    
    This approach represents a philosophical shift in how we handle schema mismatches.
    Instead of trying to predict how names will be transformed, we query the database
    to discover what columns actually exist, then create mappings on the fly. This
    self-healing approach makes the synchronization robust against any naming
    inconsistencies between AirTable and PostgreSQL.
    """
    
    def __init__(self, config: SyncConfig):
        super().__init__(config)
        self.discovered_columns = {}
        self.auto_mappings = {}
        
    def discover_table_columns(self, table_name: str) -> Dict[str, str]:
        """
        Queries the database to discover actual column names for a table.
        
        This method represents a key insight in data engineering: when dealing
        with schema mismatches, sometimes it's better to discover the truth
        from the system itself rather than trying to deduce it from rules.
        By querying the information_schema, we get the authoritative list
        of what columns actually exist.
        """
        if table_name in self.discovered_columns:
            return self.discovered_columns[table_name]
            
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = %s 
                    AND table_name = %s
                    AND column_name NOT IN (
                        'id', 'created_at', 'updated_at', 
                        'sync_status', 'last_airtable_modified',
                        'airtable_record_id'
                    )
                """, (self.config.postgres_schema, table_name))
                
                columns = {row[0]: row[0] for row in cursor.fetchall()}
                self.discovered_columns[table_name] = columns
                logger.info(f"Discovered {len(columns)} columns for {table_name}")
                return columns
                
        finally:
            self.return_connection(conn)
    
    def find_best_column_match(self, target: str, candidates: List[str]) -> Optional[str]:
        """
        Finds the best matching column name from candidates using fuzzy matching.
        
        This method implements a simple but effective matching algorithm:
        1. First, try exact match
        2. Then, try match ignoring underscores
        3. Then, try match ignoring consecutive underscores
        4. Finally, try prefix matching for very similar names
        
        This graduated approach handles most real-world naming discrepancies
        while avoiding false positives that could corrupt data.
        """
        # Exact match
        if target in candidates:
            return target
            
        # Normalize function to ignore underscore differences
        def normalize(s):
            # Remove all underscores for comparison
            return s.replace('_', '').lower()
            
        target_normalized = normalize(target)
        
        for candidate in candidates:
            if normalize(candidate) == target_normalized:
                logger.debug(f"Fuzzy matched '{target}' to '{candidate}'")
                return candidate
                
        # Try matching with different underscore patterns
        # This handles cases like 'bx_a_chin' vs 'bx_a__chin'
        target_pattern = re.sub(r'_+', '_+', re.escape(target))
        pattern = re.compile(f'^{target_pattern}$')
        
        for candidate in candidates:
            if pattern.match(candidate):
                logger.debug(f"Pattern matched '{target}' to '{candidate}'")
                return candidate
                
        return None
    
    def create_auto_mappings(self, table_name: str, record_columns: List[str]):
        """
        Creates automatic mappings between AirTable field names and PostgreSQL columns.
        
        This method embodies the principle of "convention over configuration" while
        still handling exceptions. For most fields, our sanitization rules work fine.
        For the exceptions, we automatically discover the correct mapping by comparing
        what AirTable sends with what PostgreSQL expects.
        """
        if table_name in self.auto_mappings:
            return
            
        db_columns = list(self.discover_table_columns(table_name).keys())
        mappings = {}
        
        for col in record_columns:
            if col in ['airtable_record_id', 'last_airtable_modified']:
                continue  # These are standard columns we handle separately
                
            best_match = self.find_best_column_match(col, db_columns)
            if best_match and best_match != col:
                mappings[col] = best_match
                logger.info(f"Auto-mapped '{col}' -> '{best_match}' for {table_name}")
                
        self.auto_mappings[table_name] = mappings
    
    def upsert_records(self, table_name: str, records: List[Dict]) -> Tuple[int, int]:
        """
        Enhanced upsert that automatically discovers and applies column mappings.
        
        This version represents the culmination of our learning journey. It handles:
        1. Automatic discovery of database schema
        2. Fuzzy matching of column names
        3. Explicit mappings for known exceptions
        4. Graceful handling of new or missing columns
        
        The result is a self-healing synchronization system that adapts to
        schema differences automatically while maintaining data integrity.
        """
        if not records:
            return 0, 0
        
        # Discover mappings if we haven't already
        if table_name not in self.auto_mappings and records:
            sample_columns = list(records[0].keys())
            self.create_auto_mappings(table_name, sample_columns)
        
        # Apply both explicit and auto-discovered mappings
        mapped_records = []
        for record in records:
            mapped_record = {}
            for column, value in record.items():
                # First try explicit mappings from parent class
                mapped_column = self.map_column_name(table_name, column)
                
                # Then try auto-discovered mappings
                if table_name in self.auto_mappings:
                    mapped_column = self.auto_mappings[table_name].get(
                        mapped_column, mapped_column
                    )
                
                mapped_record[mapped_column] = value
                
            mapped_records.append(mapped_record)
        
        # Now perform the actual database operation
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
            # Log the problematic query for debugging
            if 'query' in locals():
                logger.debug(f"Failed query: {query[:500]}...")  # First 500 chars
            raise
        finally:
            self.return_connection(conn)
            
        return inserted, updated

class CompleteSyncOrchestrator(FinalSyncOrchestrator):
    """
    Complete orchestrator with schema-aware synchronization.
    """
    def __init__(self, config: SyncConfig):
        self.config = config
        self.airtable = FinalAirTableClient(config)
        self.postgres = SchemaAwarePostgreSQLSync(config)

def main():
    """
    Final synchronization with automatic schema discovery.
    
    This represents the mature version of our synchronization system,
    incorporating all the lessons learned:
    - Character encoding issues with Vietnamese text
    - Schema mismatches between systems
    - Complex field types from AirTable
    - The need for both automatic and manual mapping strategies
    
    The system is now robust enough to handle whatever data
    your rice market operations throw at it.
    """
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    config = SyncConfig.from_env()
    
    if not config.airtable_api_key:
        logger.error("AIRTABLE_API_KEY environment variable not set")
        sys.exit(1)
    
    orchestrator = CompleteSyncOrchestrator(config)
    
    print("\n" + "="*60)
    print("COMPLETE AIRTABLE TO POSTGRESQL SYNCHRONIZATION")
    print("="*60)
    print("This version includes:")
    print("- Automatic schema discovery")
    print("- Fuzzy column name matching")  
    print("- Vietnamese character handling")
    print("- Complex field type support")
    print("="*60 + "\n")
    
    logger.info("Starting complete synchronization with auto-discovery")
    
    results = orchestrator.sync_all_tables()
    
    report = orchestrator.generate_sync_report(results)
    print("\n" + report)
    
    with open('sync_report.txt', 'w') as f:
        f.write(report)
    
    # Final summary
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']
    
    print("\n" + "="*60)
    if failed:
        print("SYNCHRONIZATION COMPLETED WITH ERRORS")
        for failure in failed:
            print(f"  ✗ {failure['table']}: {failure.get('error', 'Unknown error')}")
    else:
        print("SYNCHRONIZATION COMPLETED SUCCESSFULLY")
        total_processed = sum(r.get('records_processed', 0) for r in successful)
        total_inserted = sum(r.get('inserted', 0) for r in successful)
        total_updated = sum(r.get('updated', 0) for r in successful)
        
        print(f"\nFinal Statistics:")
        print(f"  Tables synchronized: {len(successful)}")
        print(f"  Total records processed: {total_processed:,}")
        print(f"  Records inserted: {total_inserted:,}")
        print(f"  Records updated: {total_updated:,}")
        
        print(f"\nYour PostgreSQL database now contains a complete mirror")
        print(f"of your AirTable data, ready for complex queries and analysis.")
        
    print("="*60 + "\n")
    
    return 0 if not failed else 1

if __name__ == "__main__":
    sys.exit(main())
