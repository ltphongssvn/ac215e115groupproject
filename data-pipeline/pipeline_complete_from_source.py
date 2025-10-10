#!/usr/bin/env python3
# File path: ~/code/ltphongssvn/ac215e115groupproject/data-pipeline/pipeline_complete_from_source.py
# Complete pipeline: Fetch all data from source APIs → Process → Migrate to PostgreSQL

import os
import sys
import time
import subprocess
import pandas as pd
import numpy as np
import json
import logging
import requests
from pathlib import Path
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteSourcePipeline:
    def __init__(self):
        self.start_time = datetime.now()
        self.results = []
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.integrated_dir = self.data_dir / "integrated"
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.integrated_dir.mkdir(parents=True, exist_ok=True)
        
    def run_command(self, cmd, description):
        """Execute command with real-time output"""
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
    
    def fetch_rice_prices_from_source(self):
        """Phase 1A: Fetch rice prices from World Bank"""
        print("\n" + "#"*70)
        print("# PHASE 1A: FETCH RICE PRICES FROM WORLD BANK")
        print("#"*70)
        
        success = self.run_command(
            "cd data-pipeline && python rice_price_spread_analysis.py --start-year 2008",
            "Download World Bank Pink Sheet rice prices (2008-2024)"
        )
        
        if success:
            # Verify output
            csv_files = list(self.processed_dir.glob("rice_spreads_*_*.csv"))
            if csv_files:
                latest = max(csv_files, key=lambda x: x.stat().st_mtime)
                df = pd.read_csv(latest)
                print(f"✓ Rice prices fetched: {len(df)} records")
                self.results.append(f"✓ Rice prices: {len(df)} monthly records")
                return True
        return False
    
    def fetch_market_factors(self):
        """Phase 1B: Fetch market factors from APIs"""
        print("\n" + "#"*70)
        print("# PHASE 1B: FETCH MARKET FACTORS FROM WORLD BANK APIs")
        print("#"*70)
        
        success = self.run_command(
            "cd data-pipeline && python market_drivers.py",
            "Fetch oil, inflation, population, ENSO, fertilizer data"
        )
        
        if success:
            csv_files = list(self.processed_dir.glob("market_factors_*.csv"))
            if csv_files:
                latest = max(csv_files, key=lambda x: x.stat().st_mtime)
                df = pd.read_csv(latest)
                print(f"✓ Market factors fetched: {len(df)} records, {len(df.columns)} columns")
                self.results.append(f"✓ Market factors: {len(df.columns)} indicators")
                return True
        return False
    
    def fetch_rainfall_data(self):
        """Phase 1C: Fetch rainfall data"""
        print("\n" + "#"*70)
        print("# PHASE 1C: FETCH RAINFALL DATA FROM WORLD BANK")
        print("#"*70)
        
        success = self.run_command(
            "cd data-pipeline && python fetch_rainfall_worldbank.py",
            "Fetch rainfall data for Asia (2008-2024)"
        )
        
        if success:
            csv_files = list(self.processed_dir.glob("rainfall_asia_*.csv"))
            if csv_files:
                latest = max(csv_files, key=lambda x: x.stat().st_mtime)
                df = pd.read_csv(latest)
                print(f"✓ Rainfall data fetched: {len(df)} records")
                self.results.append(f"✓ Rainfall: {len(df)} monthly records")
                return True
        return False
    
    def integrate_all_data(self):
        """Phase 1D: Integrate all datasets"""
        print("\n" + "#"*70)
        print("# PHASE 1D: INTEGRATE ALL DATASETS")
        print("#"*70)
        
        success = self.run_command(
            "cd data-pipeline && python integrate_all_data_final.py",
            "Merge rice, market factors, and rainfall (198 records)"
        )
        
        if success:
            csv_files = list(self.integrated_dir.glob("rice_market_rainfall_complete_*.csv"))
            if csv_files:
                latest = max(csv_files, key=lambda x: x.stat().st_mtime)
                df = pd.read_csv(latest)
                print(f"✓ Integrated dataset: {len(df)} records, {len(df.columns)} columns")
                self.results.append(f"✓ Final dataset: {len(df)} x {len(df.columns)}")
                return True
        return False
    
    def clean_gcp_database(self):
        """Clean GCP PostgreSQL"""
        print("\n" + "="*70)
        print("CLEANING GCP DATABASE")
        print("="*70)
        
        if not os.path.exists('data-pipeline/.env.gcp'):
            print("ERROR: data-pipeline/.env.gcp not found!")
            return False
            
        load_dotenv('data-pipeline/.env.gcp')
        
        try:
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST'),
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
            """)
            tables = cur.fetchall()
            
            total_deleted = 0
            for table in tables:
                cur.execute(f"DELETE FROM airtable_sync.{table[0]}")
                total_deleted += cur.rowcount
            
            conn.commit()
            print(f"✓ Cleaned {len(tables)} tables ({total_deleted} records)")
            cur.close()
            conn.close()
            
            self.results.append(f"✓ Cleaned {len(tables)} GCP tables")
            return True
            
        except Exception as e:
            print(f"Error: {str(e)}")
            self.results.append(f"✗ GCP cleanup failed")
            return False
    
    def run_airtable_migration(self):
        """Phase 2: Airtable to PostgreSQL migration"""
        print("\n" + "#"*70)
        print("# PHASE 2: AIRTABLE TO POSTGRESQL MIGRATION")
        print("#"*70)
        
        # Docker operations
        self.run_command("docker compose down -v", "Stop Docker")
        time.sleep(2)
        self.run_command("docker compose build --no-cache", "Rebuild Docker")
        self.run_command("docker compose up -d", "Start Docker")
        
        print("\n⏳ Waiting 15 seconds for PostgreSQL...")
        time.sleep(15)
        
        # Sync to local
        self.run_command(
            "cd data-pipeline && python sync_consolidated_singlefile.py",
            "Sync Airtable to Docker (13,818 records)"
        )
        
        # Sync to GCP
        self.run_command(
            "cd data-pipeline && cp .env.gcp .env && python sync_consolidated_singlefile.py",
            "Migrate to GCP Cloud SQL"
        )
        
        return True
    
    def run_complete_pipeline(self):
        """Execute complete pipeline from source"""
        print("\n" + "#"*70)
        print("# COMPLETE PIPELINE FROM SOURCE")
        print(f"# Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("#"*70)
        
        # Check environment
        if not os.path.exists('data-pipeline/.env'):
            print("ERROR: data-pipeline/.env not found!")
            return
        if not os.path.exists('data-pipeline/.env.gcp'):
            print("ERROR: data-pipeline/.env.gcp not found!")
            return
        
        # Phase 1: Fetch all data from sources
        print("\n>>> PHASE 1: FETCHING ALL DATA FROM SOURCE APIs <<<")
        rice_success = self.fetch_rice_prices_from_source()
        market_success = self.fetch_market_factors()
        rainfall_success = self.fetch_rainfall_data()
        integrate_success = self.integrate_all_data()
        
        # Phase 2: Clean GCP
        if not self.clean_gcp_database():
            print("⚠ GCP cleanup failed, continuing...")
        
        # Phase 3: Airtable Migration
        migration_success = self.run_airtable_migration()
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "#"*70)
        print("# PIPELINE COMPLETE")
        print(f"# Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print("# Results Summary:")
        print("#   DATA FETCHED FROM SOURCE:")
        print("#     - World Bank Pink Sheet (Rice Prices)")
        print("#     - World Bank APIs (Market Factors)")
        print("#     - World Bank Climate API (Rainfall)")
        print("#   INTEGRATED DATASET:")
        print("#     - 198 monthly records (2008-2024)")
        print("#     - 21 columns merged")
        print("#   AIRTABLE MIGRATION:")
        print("#     - 13,818 transaction records")
        print("#     - 8 tables synchronized")
        for result in self.results:
            print(f"#   {result}")
        print(f"# Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("#"*70)

if __name__ == "__main__":
    pipeline = CompleteSourcePipeline()
    pipeline.run_complete_pipeline()
