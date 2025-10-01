#!/usr/bin/env python3
# data-pipeline/run_sync.py
# Production-ready sync with all discovered mappings

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_final import *

class ProductionPostgreSQLSync(FinalPostgreSQLSync):
    """
    Production-ready PostgreSQL sync with comprehensive mappings.
    
    This final version includes all the mappings we've discovered through
    our iterative debugging process. In production systems, these mappings
    would typically be stored in a configuration file or database table,
    but for now we'll hard-code them based on what we've learned.
    """
    
    def __init__(self, config: SyncConfig):
        super().__init__(config)
        
        # Complete mappings discovered through our debugging journey
        self.column_mappings = {
            'contracts_hp_ng': {
                'total_price_incl_transport': 'total_price_incl__transport'
            },
            'contracts_hp_ng___2': {
                'total_price_with_vc': 'total_price_with_vc',
                'imported_quantity_n': 'imported_quantity_n'
            },
            'inventory_movements': {
                # The BX columns with their actual database names
                'bx_a_chin': 'bx_a__chin',      # BX Á Châu
                'bx_a_dng': 'bx_a_dng',          # BX Á Đông
                'bx_ngoi_ni': 'bx_ngoi_ni',      # BX ngoại/nội
                'bx_ti': 'bx_ti',                # BX tải
                'bx_tr': 'bx_tr',                # BX trữ
                'bx_thoa': 'bx___thoa',          # BX thỏa with triple underscore!
                
                # Any other potential mismatches
                'loss_13pct_from_1_6_2025': 'loss_1_3pct_from_1_6_2025',
                
                # Add field name mappings for Vietnamese text
                'ldh_kh': 'ldh_kh',  # Likely "Lệnh điều hành khách hàng"
            }
        }

class ProductionSyncOrchestrator(FinalSyncOrchestrator):
    """
    Production orchestrator with all fixes applied.
    """
    def __init__(self, config: SyncConfig):
        self.config = config
        self.airtable = FinalAirTableClient(config)
        self.postgres = ProductionPostgreSQLSync(config)

def main():
    """
    Production synchronization entry point.
    
    This is the version you would deploy to production. It includes:
    - All the column mappings we discovered
    - Proper Vietnamese character handling
    - Complex field type support
    - Incremental sync capabilities
    - Comprehensive error handling and logging
    
    The journey from our initial simple sync script to this production
    version teaches us that real-world data integration is messy.
    Success comes not from perfect initial design but from iterative
    refinement based on actual data and actual errors.
    """
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    config = SyncConfig.from_env()
    
    if not config.airtable_api_key:
        print("ERROR: AIRTABLE_API_KEY not configured")
        print("Please set your AirTable API key in data-pipeline/.env")
        return 1
    
    print("\n" + "="*70)
    print(" RICE MARKET DATA SYNCHRONIZATION SYSTEM")
    print("="*70)
    print(f" Source: AirTable Base {config.airtable_base_id}")
    print(f" Target: PostgreSQL {config.postgres_host}:{config.postgres_port}")
    print(f" Mode: {config.sync_mode.upper()}")
    print("="*70 + "\n")
    
    orchestrator = ProductionSyncOrchestrator(config)
    
    try:
        logger.info("Starting production data synchronization")
        results = orchestrator.sync_all_tables()
        
        # Generate detailed report
        report = orchestrator.generate_sync_report(results)
        print("\n" + report)
        
        # Save report to file
        with open('sync_report.txt', 'w') as f:
            f.write(report)
            
        # Calculate final statistics
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        print("\n" + "="*70)
        if failed:
            print(" ⚠ SYNCHRONIZATION COMPLETED WITH WARNINGS")
            print("-"*70)
            for failure in failed:
                table = failure['table']
                error = str(failure.get('error', 'Unknown error'))[:50]
                print(f"  ✗ {table}: {error}")
        else:
            print(" ✓ SYNCHRONIZATION COMPLETED SUCCESSFULLY")
            
        print("-"*70)
        
        # Print summary statistics
        total_processed = sum(r.get('records_processed', 0) for r in successful)
        total_inserted = sum(r.get('inserted', 0) for r in successful)
        total_updated = sum(r.get('updated', 0) for r in successful)
        total_time = sum(r.get('duration_seconds', 0) for r in results)
        
        print(f"  Tables synchronized: {len(successful)} of {len(results)}")
        print(f"  Records processed: {total_processed:,}")
        print(f"  New records: {total_inserted:,}")
        print(f"  Updated records: {total_updated:,}")
        print(f"  Total time: {total_time:.1f} seconds")
        
        if total_processed > 0:
            print(f"  Processing rate: {total_processed/total_time:.0f} records/second")
        
        print("="*70)
        
        if not failed:
            print("\n SUCCESS: Your PostgreSQL database is now synchronized with AirTable!")
            print(" You can access your data using:")
            print("   - pgAdmin: http://localhost:5051")
            print("   - Adminer: http://localhost:8081")
            print("   - psql: docker exec -it rice_market_postgres psql -U rice_admin -d rice_market_db")
        
        print()
        return 0 if not failed else 1
        
    except Exception as e:
        logger.error(f"Fatal synchronization error: {e}")
        print(f"\n ERROR: Synchronization failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
