#!/usr/bin/env python3
# data-pipeline/sync_final_complete.py
# The complete, production-ready synchronization system

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_production import *

class CompleteProductionPostgreSQLSync(ProductionPostgreSQLSync):
    """
    The final PostgreSQL sync class with all discovered mappings.
    
    This class represents the complete solution after our iterative
    debugging process. Each mapping here tells a story about a specific
    challenge we encountered and solved.
    """
    
    def __init__(self, config: SyncConfig):
        super().__init__(config)
        
        # Complete mappings including finished_goods discoveries
        self.column_mappings = {
            'contracts_hp_ng': {
                'total_price_incl_transport': 'total_price_incl__transport'
            },
            'contracts_hp_ng___2': {
                'total_price_with_vc': 'total_price_with_vc',
                'imported_quantity_n': 'imported_quantity_n'
            },
            'inventory_movements': {
                'bx_a_chin': 'bx_a__chin',
                'bx_a_dng': 'bx_a_dng',
                'bx_ngoi_ni': 'bx_ngoi_ni',
                'bx_ti': 'bx_ti',
                'bx_tr': 'bx_tr',
                'bx_thoa': 'bx___thoa',
                'loss_13pct_from_1_6_2025': 'loss_1_3pct_from_1_6_2025',
            },
            'finished_goods': {
                # The quantity field mappings with triple underscores
                's_lng_theo_u_bao_trong_gi': 's_lng_theo_u_bao___trong_gi',
                's_lng_theo_u_bao_ngoi_gi': 's_lng_theo_u_bao___ngoi_gi',
                's_lng_theo_u_bao_trong_gi_ca_2': 's_lng_theo_u_bao___trong_gi_ca_2',
                's_lng_theo_u_bao_ngoi_gi_ca_2': 's_lng_theo_u_bao___ngoi_gi_ca_2',
            }
        }

class FinalCompleteOrchestrator(RobustProductionOrchestrator):
    """
    The final orchestrator with all fixes, validations, and mappings.
    """
    def __init__(self, config: SyncConfig):
        self.config = config
        self.airtable = ValidatingAirTableClient(config)
        self.postgres = CompleteProductionPostgreSQLSync(config)

def main():
    """
    The final, complete synchronization system.
    
    This represents the end of our journey from a simple theoretical sync
    script to a battle-tested production system. The path we took teaches
    us several critical lessons about building real-world data pipelines:
    
    1. Real data is messy. Vietnamese characters, impossible percentages,
       inconsistent naming - these are the norm, not the exception.
       
    2. Iterative debugging is the only way to build robust systems. Each
       error we encountered revealed something we couldn't have predicted
       from documentation alone.
       
    3. Production code isn't about being perfect; it's about being resilient.
       Our system now handles errors gracefully, validates data, and adapts
       to inconsistencies.
       
    4. Understanding the business context matters. Those BX columns represent
       warehouse locations. The percentage fields track rice quality metrics.
       This context helps us make better technical decisions.
    """
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    config = SyncConfig.from_env()
    
    if not config.airtable_api_key:
        print("ERROR: Missing AirTable API key")
        return 1
    
    print("\n" + "="*70)
    print(" RICE MARKET DATA SYNCHRONIZATION SYSTEM")
    print(" Final Production Version - All Issues Resolved")
    print("="*70)
    print(f" Source: AirTable (Base: {config.airtable_base_id})")
    print(f" Target: PostgreSQL ({config.postgres_host}:{config.postgres_port})")
    print(f" Database: {config.postgres_database}")
    print(f" Mode: {config.sync_mode.upper()}")
    print("="*70 + "\n")
    
    orchestrator = FinalCompleteOrchestrator(config)
    
    try:
        logger.info("Starting final complete synchronization")
        
        # Run the synchronization
        results = orchestrator.sync_all_tables()
        
        # Generate and save report
        report = orchestrator.generate_sync_report(results)
        print("\n" + report)
        
        with open('sync_report.txt', 'w') as f:
            f.write(report)
        
        # Calculate statistics
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        print("\n" + "="*70)
        
        if not failed:
            print(" ✓✓✓ COMPLETE SUCCESS! ✓✓✓")
            print("="*70)
            
            # Calculate comprehensive statistics
            total_processed = sum(r.get('records_processed', 0) for r in successful)
            total_inserted = sum(r.get('inserted', 0) for r in successful)
            total_updated = sum(r.get('updated', 0) for r in successful)
            total_time = sum(r.get('duration_seconds', 0) for r in results)
            
            print(f"\n SYNCHRONIZATION SUMMARY:")
            print(f" • Tables synchronized: {len(successful)}/8")
            print(f" • Total records processed: {total_processed:,}")
            print(f" • New records inserted: {total_inserted:,}")
            print(f" • Records updated: {total_updated:,}")
            print(f" • Total processing time: {total_time:.1f} seconds")
            
            if total_processed > 0 and total_time > 0:
                rate = total_processed / total_time
                print(f" • Processing rate: {rate:.0f} records/second")
            
            # Breakdown by table
            print(f"\n TABLE BREAKDOWN:")
            for result in successful:
                if result['records_processed'] > 0:
                    table = result['table']
                    count = result['records_processed']
                    print(f" • {table}: {count:,} records")
            
            print(f"\n YOUR DATA IS NOW FULLY SYNCHRONIZED!")
            print(f" The PostgreSQL database contains a complete mirror of your")
            print(f" AirTable data, ready for complex queries and analysis.")
            
            print(f"\n ACCESS YOUR DATA:")
            print(f" • pgAdmin: http://localhost:5051")
            print(f"   (login: admin@ricemarket.local / admin123)")
            print(f" • Adminer: http://localhost:8081")
            print(f"   (server: rice_market_postgres, user: rice_admin)")
            print(f" • Command line:")
            print(f"   docker exec -it rice_market_postgres psql -U rice_admin -d rice_market_db")
            
            print(f"\n EXAMPLE QUERIES TO TRY:")
            print(f" • Total inventory by location:")
            print(f"   SELECT SUM(closing_balance_tons) FROM airtable_sync.inventory_movements;")
            print(f" • Recent contracts:")
            print(f"   SELECT * FROM airtable_sync.contracts_hp_ng ORDER BY contract_date DESC LIMIT 10;")
            print(f" • Customer summary:")
            print(f"   SELECT COUNT(*) FROM airtable_sync.customers;")
            
            print(f"\n NEXT STEPS:")
            print(f" 1. Change SYNC_MODE=incremental in .env for faster future syncs")
            print(f" 2. Schedule this script to run periodically (e.g., every hour)")
            print(f" 3. Consider setting up monitoring for sync failures")
            print(f" 4. Deploy to Google Cloud for production use")
            
        else:
            print(" ⚠ Synchronization completed with errors")
            for failure in failed:
                print(f" ✗ {failure['table']}: {failure.get('error', 'Unknown error')}")
        
        print("="*70 + "\n")
        
        return 0 if not failed else 1
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
