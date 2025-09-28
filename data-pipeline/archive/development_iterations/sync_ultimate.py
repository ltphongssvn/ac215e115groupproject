#!/usr/bin/env python3
# data-pipeline/sync_ultimate.py
# The ultimate synchronization with complete field name handling

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_final_complete import *

class UltimateAirTableClient(ValidatingAirTableClient):
    """
    The ultimate AirTable client that handles all field name edge cases.
    
    This version specifically addresses fields that start with numbers after
    Vietnamese text is removed, ensuring they get proper prefixes to maintain
    SQL compatibility.
    """
    
    def _sanitize_column_name(self, name: str) -> str:
        """
        Enhanced sanitization that prevents invalid SQL identifiers.
        
        This method ensures that after all transformations, the resulting
        column name is valid SQL. The key insight is that if a name would
        start with a digit after sanitization, we need to preserve some
        prefix from the original name to maintain validity.
        """
        # First apply the standard sanitization
        safe = super()._sanitize_column_name(name)
        
        # Check if the result starts with a digit (invalid SQL)
        if safe and safe[0].isdigit():
            # For time-based fields, prefix with 'n_' (from "Đêm"/night)
            # This matches what the DDL generation did
            if 'h' in safe and any(c.isdigit() for c in safe):
                safe = 'n_' + safe
            else:
                # For other numeric-starting fields, prefix with 'f_' (field)
                safe = 'f_' + safe
                
        return safe

class UltimateProductionPostgreSQLSync(CompleteProductionPostgreSQLSync):
    """
    The ultimate PostgreSQL sync with all mappings including shift times.
    """
    
    def __init__(self, config: SyncConfig):
        super().__init__(config)
        
        # Add the finished_goods time-based field mappings
        self.column_mappings['finished_goods'].update({
            # Shift time mappings
            'n_16h30_19h': 'n_16h30_19h',  # Already correct after fix
            'n_19h_7h': 'n_19h_7h',  # Already correct after fix
            
            # Other discovered mappings from looking at the data
            'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_1': 'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_1',
            'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_2': 'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_2',
            'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_3': 'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_3',
            'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_4': 'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_4',
        })

class UltimateSyncOrchestrator(FinalCompleteOrchestrator):
    """
    The ultimate orchestrator that brings everything together.
    """
    def __init__(self, config: SyncConfig):
        self.config = config
        self.airtable = UltimateAirTableClient(config)
        self.postgres = UltimateProductionPostgreSQLSync(config)

def main():
    """
    The ultimate synchronization entry point.
    
    This represents the true culmination of our journey. We've learned that
    building production data pipelines isn't about writing perfect code from
    the start - it's about methodically working through each challenge,
    understanding why it occurs, and building solutions that handle the
    messy reality of production data.
    
    Our rice market database tells a story through its field names:
    - Vietnamese business terminology mixed with English
    - Shift times tracking 24-hour operations
    - Quality metrics stored in unexpected formats
    - Warehouse codes representing physical locations
    
    Each error we encountered taught us something valuable about the data
    and the business it represents.
    """
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    config = SyncConfig.from_env()
    
    if not config.airtable_api_key:
        print("ERROR: AirTable API key not configured")
        return 1
    
    print("\n" + "="*70)
    print(" 🌾 RICE MARKET DATA SYNCHRONIZATION SYSTEM 🌾")
    print(" Ultimate Production Version")
    print("="*70)
    print(f" Source: AirTable (Base: {config.airtable_base_id})")
    print(f" Target: PostgreSQL ({config.postgres_host}:{config.postgres_port})")
    print(f" Database: {config.postgres_database}")
    print(f" Schema: {config.postgres_schema}")
    print(f" Mode: {config.sync_mode.upper()}")
    print("="*70)
    
    orchestrator = UltimateSyncOrchestrator(config)
    
    try:
        start_time = datetime.now()
        logger.info("Starting ultimate synchronization")
        
        results = orchestrator.sync_all_tables()
        
        # Generate comprehensive report
        report = orchestrator.generate_sync_report(results)
        print("\n" + report)
        
        with open('sync_report.txt', 'w') as f:
            f.write(report)
            f.write(f"\n\nGenerated at: {datetime.now()}")
        
        # Process results
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        print("\n" + "="*70)
        
        if not failed:
            print(" ✅ COMPLETE SUCCESS - ALL DATA SYNCHRONIZED! ✅")
            print("="*70)
            
            # Calculate comprehensive metrics
            total_processed = sum(r.get('records_processed', 0) for r in successful)
            total_inserted = sum(r.get('inserted', 0) for r in successful)
            total_updated = sum(r.get('updated', 0) for r in successful)
            total_time = (datetime.now() - start_time).total_seconds()
            
            print(f"\n 📊 SYNCHRONIZATION METRICS:")
            print(f" • Tables synchronized: {len(successful)}/8")
            print(f" • Total records processed: {total_processed:,}")
            print(f" • New records inserted: {total_inserted:,}")
            print(f" • Records updated: {total_updated:,}")
            print(f" • Total processing time: {total_time:.1f} seconds")
            
            if total_processed > 0 and total_time > 0:
                print(f" • Processing rate: {total_processed/total_time:.0f} records/second")
            
            print(f"\n 📋 TABLE-BY-TABLE BREAKDOWN:")
            for result in successful:
                if result['records_processed'] > 0:
                    table = result['table'].replace('_', ' ').title()
                    count = result['records_processed']
                    inserted = result.get('inserted', 0)
                    updated = result.get('updated', 0)
                    duration = result.get('duration_seconds', 0)
                    print(f" • {table}: {count:,} records ({inserted} new, {updated} updated) in {duration:.1f}s")
            
            print(f"\n 🎉 SUCCESS! Your PostgreSQL database is fully synchronized!")
            print(f" The rice market data is now available for:")
            print(f" • Complex SQL queries and reporting")
            print(f" • Real-time analytics dashboards")
            print(f" • Integration with other systems")
            print(f" • Backup and disaster recovery")
            
            print(f"\n 🔗 ACCESS YOUR DATA:")
            print(f" • pgAdmin web interface: http://localhost:5051")
            print(f"   Login: admin@ricemarket.local / admin123")
            print(f" • Adminer interface: http://localhost:8081")
            print(f"   Server: rice_market_postgres, User: rice_admin, Pass: localdev123")
            print(f" • Command line:")
            print(f"   docker exec -it rice_market_postgres psql -U rice_admin -d rice_market_db")
            
            print(f"\n 🔍 INTERESTING QUERIES TO EXPLORE YOUR DATA:")
            print(f" • Total rice inventory across all warehouses:")
            print(f"   SELECT SUM(closing_balance_tons) FROM airtable_sync.inventory_movements;")
            print(f" • Customer distribution:")
            print(f"   SELECT address, COUNT(*) FROM airtable_sync.customers GROUP BY address;")
            print(f" • Recent contract values:")
            print(f"   SELECT contract_date, SUM(total_amount) FROM airtable_sync.contracts_hp_ng")
            print(f"   WHERE contract_date > CURRENT_DATE - INTERVAL '30 days' GROUP BY contract_date;")
            print(f" • Production by shift:")
            print(f"   SELECT COUNT(*), SUM(n_16h30_19h) as evening_shift, SUM(n_19h_7h) as night_shift")
            print(f"   FROM airtable_sync.finished_goods;")
            
            print(f"\n 🚀 NEXT STEPS FOR PRODUCTION:")
            print(f" 1. Update .env: Set SYNC_MODE=incremental for faster updates")
            print(f" 2. Schedule syncs: Add to crontab for hourly/daily runs")
            print(f" 3. Monitor health: Set up alerts for sync failures")
            print(f" 4. Deploy to cloud: Migrate to Google Cloud SQL when ready")
            print(f" 5. Build dashboards: Connect Tableau/PowerBI to PostgreSQL")
            
        else:
            print(" ⚠️  Synchronization completed with errors")
            for failure in failed:
                print(f" ✗ {failure['table']}: {failure.get('error', 'Unknown error')}")
            print("\n Check sync.log for detailed error information")
            
        print("="*70)
        print()
        
        return 0 if not failed else 1
        
    except Exception as e:
        logger.error(f"Fatal synchronization error: {e}", exc_info=True)
        print(f"\n ❌ FATAL ERROR: {e}")
        print(f" Check sync.log for full stack trace")
        return 1

if __name__ == "__main__":
    sys.exit(main())
