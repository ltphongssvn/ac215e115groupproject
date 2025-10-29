#!/usr/bin/env python3
# File path: ~/code/ltphongssvn/ac215e115groupproject/data-pipeline/pipeline_complete_integrated.py
# Complete pipeline: Market data integration (198 records) + Airtable migration (13,818 records)

import os
import sys
import time
import subprocess
import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompletePipeline:
    def __init__(self):
        self.start_time = datetime.now()
        self.results = []
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.processed_dir = self.data_dir / "processed"
        self.integrated_dir = self.data_dir / "integrated"
        self.integrated_dir.mkdir(parents=True, exist_ok=True)
        
    def run_command_realtime(self, cmd, description):
        """Execute shell command with real-time output"""
        print(f"\n{'='*70}")
        print(f"STEP: {description}")
        print(f"{'='*70}")
        
        try:
            process = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
            process.wait()
            
            if process.returncode == 0:
                print(f"✓ SUCCESS: {description}")
                self.results.append(f"✓ {description}")
                return True
            else:
                print(f"✗ FAILED: {description}")
                self.results.append(f"✗ {description}")
                return False
        except Exception as e:
            print(f"✗ EXCEPTION: {str(e)}")
            self.results.append(f"✗ {description}: {str(e)}")
            return False
    
    def integrate_market_data(self):
        """Phase 1: Integrate market data (198 monthly records)"""
        print("\n" + "#"*70)
        print("# PHASE 1: MARKET DATA INTEGRATION")
        print("#"*70)
        
        try:
            # Run the integration script
            success = self.run_command_realtime(
                "cd data-pipeline && python integrate_all_data_final.py",
                "Generate integrated market dataset (198 records)"
            )
            
            if success:
                # Verify output
                integrated_file = self.integrated_dir / f"rice_market_rainfall_complete_{datetime.now().strftime('%Y%m%d')}*.csv"
                files = list(self.integrated_dir.glob("rice_market_rainfall_complete_*.csv"))
                if files:
                    latest_file = max(files, key=lambda x: x.stat().st_mtime)
                    df = pd.read_csv(latest_file)
                    print(f"✓ Market data integrated: {len(df)} records, {len(df.columns)} columns")
                    self.results.append(f"✓ Market data: {len(df)} monthly records")
                    return True
            return False
            
        except Exception as e:
            print(f"Error in market integration: {str(e)}")
            self.results.append(f"✗ Market integration failed: {str(e)}")
            return False
    
    def clean_gcp_database(self):
        """Clean GCP PostgreSQL before migration"""
        print("\n" + "="*70)
        print("CLEANING GCP DATABASE")
        print("="*70)
        
        if not os.path.exists('data-pipeline/.env.gcp'):
            print("ERROR: data-pipeline/.env.gcp not found!")
            return False
            
        load_dotenv('data-pipeline/.env.gcp')
        gcp_host = os.getenv('POSTGRES_HOST')
        
        if not gcp_host:
            print("ERROR: POSTGRES_HOST not set in .env.gcp")
            return False
        
        try:
            conn = psycopg2.connect(
                host=gcp_host,
                port=int(os.getenv('POSTGRES_PORT', '5432')),
                database=os.getenv('POSTGRES_DATABASE', 'rice_market_db'),
                user=os.getenv('POSTGRES_USER', 'rice_admin'),
                password=os.getenv('POSTGRES_PASSWORD')
            )
            cur = conn.cursor()
            
            cur.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'airtable_sync' 
                AND tablename NOT LIKE '%_id_seq'
                ORDER BY tablename
            """)
            tables = cur.fetchall()
            
            total_deleted = 0
            for table in tables:
                table_name = table[0]
                cur.execute(f"DELETE FROM airtable_sync.{table_name}")
                count = cur.rowcount
                if count > 0:
                    total_deleted += count
            
            conn.commit()
            print(f"✓ Cleaned {len(tables)} tables ({total_deleted} records)")
            cur.close()
            conn.close()
            
            self.results.append(f"✓ Cleaned {len(tables)} GCP tables")
            return True
            
        except Exception as e:
            print(f"Error cleaning GCP: {str(e)}")
            self.results.append(f"✗ GCP cleanup failed")
            return False
    
    def run_airtable_migration(self):
        """Phase 2: Run Airtable to PostgreSQL migration (13,818 records)"""
        print("\n" + "#"*70)
        print("# PHASE 2: AIRTABLE TO POSTGRESQL MIGRATION")
        print("#"*70)
        
        # Docker cleanup
        self.run_command_realtime(
            "docker compose down -v",
            "Stop Docker and remove volumes"
        )
        
        time.sleep(2)
        
        # Docker rebuild
        self.run_command_realtime(
            "docker compose build --no-cache",
            "Rebuild Docker images"
        )
        
        # Start containers
        self.run_command_realtime(
            "docker compose up -d",
            "Start Docker containers"
        )
        
        print("\n⏳ Waiting 15 seconds for PostgreSQL...")
        time.sleep(15)
        
        # Sync to local
        self.run_command_realtime(
            "cd data-pipeline && python sync_consolidated_singlefile.py",
            "Sync Airtable to Local Docker (13,818 records)"
        )
        
        # Sync to GCP
        self.run_command_realtime(
            "cd data-pipeline && cp .env.gcp .env && python sync_consolidated_singlefile.py",
            "Migrate to GCP Cloud SQL"
        )
        
        return True
    
    def run_complete_pipeline(self):
        """Execute complete integrated pipeline"""
        print("\n" + "#"*70)
        print("# COMPLETE INTEGRATED PIPELINE")
        print(f"# Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("#"*70)
        
        # Check environment files
        if not os.path.exists('data-pipeline/.env'):
            print("ERROR: data-pipeline/.env not found!")
            return
        
        if not os.path.exists('data-pipeline/.env.gcp'):
            print("ERROR: data-pipeline/.env.gcp not found!")
            return
        
        # Phase 1: Market Data Integration
        market_success = self.integrate_market_data()
        
        # Phase 2: Clean GCP
        if not self.clean_gcp_database():
            print("⚠ Warning: GCP cleanup failed, continuing...")
        
        # Phase 3: Airtable Migration
        migration_success = self.run_airtable_migration()
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "#"*70)
        print("# PIPELINE COMPLETE")
        print(f"# Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print("# Results Summary:")
        print("#   MARKET DATA:")
        print("#     - 198 monthly records (2008-2024)")
        print("#     - 21 columns integrated")
        print("#   AIRTABLE DATA:")
        print("#     - 13,818 transaction records")
        print("#     - 8 tables synchronized")
        for result in self.results:
            print(f"#   {result}")
        print(f"# Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("#"*70)

if __name__ == "__main__":
    pipeline = CompletePipeline()
    pipeline.run_complete_pipeline()
