#!/usr/bin/env python3
# data-pipeline/airtable_sync_fixed.py
# Fixed version of the synchronization script that handles complex field types

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the original sync module
from airtable_sync import *

class FixedAirTableClient(AirTableClient):
    """
    Enhanced AirTable client that properly handles complex field types.
    
    This fix addresses the issue where some AirTable fields return dictionaries
    or complex objects instead of simple values. The commodities table, for instance,
    might have attachment fields (photos) or complex relationship fields that
    include metadata beyond just record IDs.
    """
    
    def transform_record(self, record: Dict, table_name: str) -> Dict:
        """
        Transforms an AirTable record into PostgreSQL-compatible format.
        
        This enhanced version handles various field types more robustly:
        - Simple values (strings, numbers, booleans)
        - Lists of record IDs (relationships)
        - Lists of complex objects (attachments, complex relationships)
        - Dictionary objects (single attachments, metadata)
        """
        transformed = {
            'airtable_record_id': record['id'],
            'last_airtable_modified': record.get('createdTime')
        }
        
        fields = record.get('fields', {})
        
        for field_name, value in fields.items():
            # Convert field name to PostgreSQL column name
            pg_column = self._sanitize_column_name(field_name)
            
            # Handle different value types with more sophistication
            if value is None:
                transformed[pg_column] = None
                
            elif isinstance(value, list):
                # Check if this is a list of record IDs (relationship field)
                if value and isinstance(value[0], str) and value[0].startswith('rec'):
                    # This is a relationship field - skip it for now
                    # These will be handled in a separate junction table sync
                    continue
                    
                elif value and isinstance(value[0], dict):
                    # This could be attachments or complex relationships
                    # For now, we'll store just the essential data
                    if 'id' in value[0]:
                        # Extract just the IDs if they exist
                        extracted_ids = [item.get('id') for item in value if 'id' in item]
                        if extracted_ids and extracted_ids[0].startswith('rec'):
                            # These are relationship IDs, skip them
                            continue
                    
                    # For other complex lists (like attachments), store as JSON
                    # but try to extract the most relevant information
                    if 'url' in value[0]:
                        # This looks like attachment data - extract URLs
                        urls = [item.get('url') for item in value if 'url' in item]
                        transformed[pg_column] = Json(urls) if urls else None
                    else:
                        # Store the whole structure as JSON for other complex types
                        transformed[pg_column] = Json(value)
                else:
                    # Simple list of values
                    transformed[pg_column] = Json(value)
                    
            elif isinstance(value, dict):
                # Single complex object (like a single attachment or formula result)
                # Store as JSON but try to extract key information if possible
                if 'url' in value:
                    # Single attachment - store just the URL
                    transformed[pg_column] = value.get('url')
                else:
                    # Store the whole dictionary as JSON
                    transformed[pg_column] = Json(value)
                    
            elif isinstance(value, (int, float, str, bool)):
                # Simple scalar values
                transformed[pg_column] = value
                
            else:
                # Fallback for any other type - store as JSON
                transformed[pg_column] = Json(value)
                
        return transformed

# Patch the original orchestrator to use our fixed client
class FixedSyncOrchestrator(SyncOrchestrator):
    def __init__(self, config: SyncConfig):
        self.config = config
        self.airtable = FixedAirTableClient(config)  # Use our fixed client
        self.postgres = PostgreSQLSync(config)

def main():
    """
    Main entry point with the fixed synchronization logic.
    """
    # Load configuration from environment
    from dotenv import load_dotenv
    load_dotenv('.env')  # Load from current directory since we're in data-pipeline
    
    config = SyncConfig.from_env()
    
    # Validate configuration
    if not config.airtable_api_key:
        logger.error("AIRTABLE_API_KEY environment variable not set")
        sys.exit(1)
    
    # Create orchestrator with our fixed client and run sync
    orchestrator = FixedSyncOrchestrator(config)
    
    logger.info("Starting AirTable to PostgreSQL synchronization (with fixes)")
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
