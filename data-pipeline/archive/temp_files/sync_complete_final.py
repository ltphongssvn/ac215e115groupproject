#!/usr/bin/env python3
# data-pipeline/sync_complete_final.py
# The complete production synchronization with all discovered mappings

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_ultimate import *

class CompleteProductionSync(UltimateProductionPostgreSQLSync):
    """
    The complete synchronization class with all mappings discovered through our journey.
    
    This class represents the accumulation of all our debugging efforts. Each mapping
    tells a story about a specific challenge we encountered and solved together.
    """
    
    def __init__(self, config: SyncConfig):
        super().__init__(config)
        
        # Complete comprehensive mappings based on all our discoveries
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
                # Quantity field mappings with triple underscores
                's_lng_theo_u_bao_trong_gi': 's_lng_theo_u_bao___trong_gi',
                's_lng_theo_u_bao_ngoi_gi': 's_lng_theo_u_bao___ngoi_gi',
                's_lng_theo_u_bao_trong_gi_ca_2': 's_lng_theo_u_bao___trong_gi_ca_2',
                's_lng_theo_u_bao_ngoi_gi_ca_2': 's_lng_theo_u_bao___ngoi_gi_ca_2',
                
                # Price field mappings with double underscores before "ch"
                'ngoi_gi_75k_ch_nht_ca_1': 'ngoi_gi_75k__ch_nht_ca_1',
                'ngoi_gi_75k_ch_nht_ca_4': 'ngoi_gi_75k__ch_nht_ca_4',
                'trong_gi_57k_ca_4': 'trong_gi_57k_ca_4',
                
                # Time-based fields are already handled by UltimateAirTableClient
                # which adds 'n_' prefix for fields starting with numbers
            }
        }

class FinalCompleteOrchestrator(UltimateSyncOrchestrator):
    """
    The final orchestrator using our complete sync implementation.
    """
    def __init__(self, config: SyncConfig):
        self.config = config
        self.airtable = UltimateAirTableClient(config)
        self.postgres = CompleteProductionSync(config)

def main():
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    config = SyncConfig.from_env()
    
    if not config.airtable_api_key:
        print("ERROR: AirTable API key not configured")
        return 1
    
    print("\n" + "="*70)
    print(" RICE MARKET DATA SYNCHRONIZATION")
    print(" Complete Production System with All Mappings")
    print("="*70)
    print(f" AirTable Base: {config.airtable_base_id}")
    print(f" PostgreSQL: {config.postgres_database} @ {config.postgres_host}:{config.postgres_port}")
    print(f" Sync Mode: {config.sync_mode.upper()}")
    print("="*70 + "\n")
    
    orchestrator = FinalCompleteOrchestrator(config)
    
    try:
        start_time = datetime.now()
        results = orchestrator.sync_all_tables()
        
        report = orchestrator.generate_sync_report(results)
        print("\n" + report)
        
        with open('sync_report_final.txt', 'w') as f:
            f.write(report)
            f.write(f"\n\nCompleted at: {datetime.now()}")
            f.write("\n\nThis synchronization includes fixes for:")
            f.write("\n- Vietnamese character handling")
            f.write("\n- Column naming inconsistencies")
            f.write("\n- Numeric overflow protection")
            f.write("\n- SQL identifier compliance")
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        if not failed:
            total_records = sum(r.get('records_processed', 0) for r in successful)
            total_time = (datetime.now() - start_time).total_seconds()
            
            print("\n" + "="*70)
            print(" SUCCESS - All tables synchronized!")
            print("="*70)
            print(f" Total records: {total_records:,}")
            print(f" Total time: {total_time:.1f} seconds")
            print(f" Processing rate: {total_records/total_time:.0f} records/second")
            print("\n Your rice market data is now available in PostgreSQL!")
            print(" Access at: http://localhost:5051 (pgAdmin)")
            print("            http://localhost:8081 (Adminer)")
            print("="*70 + "\n")
            
            # Now update the .env file for future incremental syncs
            print(" Updating configuration for incremental syncs...")
            env_path = 'data-pipeline/.env'
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            with open(env_path, 'w') as f:
                for line in lines:
                    if line.startswith('SYNC_MODE='):
                        f.write('SYNC_MODE=incremental  # Changed after successful full sync\n')
                    else:
                        f.write(line)
            
            print(" Configuration updated. Future syncs will be incremental.")
            
        else:
            print("\n Synchronization failed. Check errors above.")
            
        return 0 if not failed else 1
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
