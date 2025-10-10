#!/usr/bin/env python3
# data-pipeline/sync_production.py
# Production sync with data validation and transformation

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_sync import *

class ValidatingAirTableClient(FinalAirTableClient):
    """
    AirTable client that validates and transforms data during sync.
    
    This class handles data quality issues that can arise when syncing
    between flexible systems like AirTable and strict systems like PostgreSQL.
    It validates numeric ranges, transforms percentages, and ensures data
    fits within database constraints.
    """
    
    def transform_record(self, record: Dict, table_name: str) -> Dict:
        """
        Enhanced transform that validates and corrects data values.
        """
        # First do the standard transformation
        transformed = super().transform_record(record, table_name)
        
        # Now apply table-specific validations and transformations
        if table_name == 'inventory_movements':
            # Handle percentage fields that might be stored as whole numbers
            pct_fields = ['fat_pct', 'moisture_pct']
            
            for field in pct_fields:
                if field in transformed and transformed[field] is not None:
                    value = transformed[field]
                    if isinstance(value, (int, float)):
                        # If value is > 1, assume it's a whole number percentage
                        # and convert to decimal (e.g., 85 -> 0.85)
                        if value > 1:
                            transformed[field] = value / 100.0
                        
                        # Ensure it fits in DECIMAL(5,3) - max value is 99.999
                        if transformed[field] > 99.999:
                            logger.warning(f"Value {value} for {field} exceeds max, capping at 99.999")
                            transformed[field] = 99.999
                        elif transformed[field] < -99.999:
                            logger.warning(f"Value {value} for {field} below min, capping at -99.999")
                            transformed[field] = -99.999
                            
        elif table_name == 'contracts_hp_ng___2':
            # Similar handling for contract percentage fields
            pct_fields = ['protein_pct', 'ash_pct', 'fibre_pct', 
                         'fat_pct', 'moisture_pct', 'starch_pct', 'acid_value_pct']
            
            for field in pct_fields:
                if field in transformed and transformed[field] is not None:
                    value = transformed[field]
                    if isinstance(value, (int, float)):
                        if value > 1:
                            transformed[field] = value / 100.0
                        
                        if transformed[field] > 99.999:
                            logger.warning(f"Value {value} for {field} exceeds max, capping at 99.999")
                            transformed[field] = 99.999
                        elif transformed[field] < -99.999:
                            transformed[field] = -99.999
                            
        return transformed

class RobustProductionOrchestrator(ProductionSyncOrchestrator):
    """
    Final production orchestrator with all fixes and validations.
    """
    def __init__(self, config: SyncConfig):
        self.config = config
        self.airtable = ValidatingAirTableClient(config)
        self.postgres = ProductionPostgreSQLSync(config)

def main():
    """
    Production-ready synchronization with complete error handling.
    
    This final version represents a battle-tested synchronization system
    that handles all the complexities we've discovered:
    - Vietnamese character encoding
    - Column name mismatches
    - Numeric overflow issues
    - Data type conversions
    - Incremental synchronization
    
    The journey to this point teaches us that building robust data
    pipelines requires iterative refinement based on real data and
    real errors. Each failure revealed something about the data that
    documentation alone couldn't tell us.
    """
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    config = SyncConfig.from_env()
    
    if not config.airtable_api_key:
        print("ERROR: AIRTABLE_API_KEY not configured")
        return 1
    
    print("\n" + "="*70)
    print(" RICE MARKET DATA SYNCHRONIZATION SYSTEM")
    print(" Production Version with Full Data Validation")
    print("="*70)
    print(f" Source: AirTable Base {config.airtable_base_id}")
    print(f" Target: PostgreSQL {config.postgres_host}:{config.postgres_port}")
    print(f" Features: Data validation, numeric overflow protection")
    print("="*70 + "\n")
    
    orchestrator = RobustProductionOrchestrator(config)
    
    try:
        logger.info("Starting production sync with data validation")
        results = orchestrator.sync_all_tables()
        
        report = orchestrator.generate_sync_report(results)
        print("\n" + report)
        
        with open('sync_report.txt', 'w') as f:
            f.write(report)
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        print("\n" + "="*70)
        if not failed:
            print(" ✓ SYNCHRONIZATION COMPLETED SUCCESSFULLY!")
            print("="*70)
            
            total_processed = sum(r.get('records_processed', 0) for r in successful)
            total_inserted = sum(r.get('inserted', 0) for r in successful)
            total_updated = sum(r.get('updated', 0) for r in successful)
            total_time = sum(r.get('duration_seconds', 0) for r in results)
            
            print(f"\n Final Statistics:")
            print(f"   • Tables synchronized: {len(successful)}")
            print(f"   • Total records: {total_processed:,}")
            print(f"   • New insertions: {total_inserted:,}")
            print(f"   • Updates: {total_updated:,}")
            print(f"   • Processing time: {total_time:.1f} seconds")
            
            if total_processed > 0:
                print(f"   • Throughput: {total_processed/total_time:.0f} records/second")
            
            print(f"\n Your data is now available in PostgreSQL!")
            print(f" Access options:")
            print(f"   • pgAdmin: http://localhost:5051")
            print(f"   • Adminer: http://localhost:8081")
            print(f"   • Command line: docker exec -it rice_market_postgres psql -U rice_admin -d rice_market_db")
            
            print(f"\n Next steps:")
            print(f"   1. Review the sync_report.txt for details")
            print(f"   2. Set SYNC_MODE=incremental in .env for future syncs")
            print(f"   3. Schedule this script to run periodically for continuous sync")
            
        else:
            print(" ⚠ Synchronization completed with issues")
            for failure in failed:
                print(f"   ✗ {failure['table']}: {str(failure.get('error', 'Unknown'))[:60]}")
                
        print("="*70 + "\n")
        return 0 if not failed else 1
        
    except Exception as e:
        logger.error(f"Synchronization failed: {e}")
        print(f"\n ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
