#!/usr/bin/env python3
# File path: ~/code/ltphongssvn/ac215e115groupproject/data-pipeline/pipeline_full_migration.py
# End-to-end pipeline: Clean GCP DB -> Docker rebuild -> Local sync -> GCP migration

import os
import sys
import time
import subprocess
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

class PipelineMigration:
    def __init__(self):
        self.start_time = datetime.now()
        self.results = []
        
    def run_command_realtime(self, cmd, description):
        """Execute shell command with real-time output"""
        print(f"\n{'='*70}")
        print(f"STEP: {description}")
        print(f"Command: {cmd}")
        print(f"{'='*70}")
        
        try:
            process = subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
            
            process.wait()
            
            if process.returncode == 0:
                print(f"\n✓ SUCCESS: {description}")
                self.results.append(f"✓ {description}")
                return True
            else:
                print(f"\n✗ FAILED: {description} (exit code: {process.returncode})")
                self.results.append(f"✗ {description}")
                return False
                
        except Exception as e:
            print(f"\n✗ EXCEPTION: {str(e)}")
            self.results.append(f"✗ {description}: {str(e)}")
            return False
    
    def clean_gcp_database(self):
        """Clean all records from GCP PostgreSQL"""
        print("\n" + "="*70)
        print("CLEANING GCP DATABASE")
        print("="*70)
        
        # Load GCP config
        if not os.path.exists('data-pipeline/.env.gcp'):
            print("ERROR: data-pipeline/.env.gcp not found!")
            print("Please create it from .env.gcp.example")
            return False
            
        load_dotenv('data-pipeline/.env.gcp')
        
        gcp_host = os.getenv('POSTGRES_HOST')
        if not gcp_host:
            print("ERROR: POSTGRES_HOST not set in .env.gcp")
            return False
        
        try:
            print(f"Connecting to GCP Cloud SQL at {gcp_host}...")
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
            
            print(f"Found {len(tables)} tables to clean")
            
            total_deleted = 0
            for table in tables:
                table_name = table[0]
                cur.execute(f"DELETE FROM airtable_sync.{table_name}")
                count = cur.rowcount
                if count > 0:
                    print(f"  ✓ Deleted {count} rows from {table_name}")
                    total_deleted += count
            
            conn.commit()
            print(f"\nTotal records deleted: {total_deleted}")
            cur.close()
            conn.close()
            
            self.results.append(f"✓ Cleaned {len(tables)} GCP tables ({total_deleted} records)")
            return True
            
        except Exception as e:
            print(f"Error cleaning GCP: {str(e)}")
            self.results.append(f"✗ GCP cleanup failed: {str(e)}")
            return False
    
    def run_pipeline(self):
        """Execute complete pipeline"""
        print("\n" + "#"*70)
        print("# FULL MIGRATION PIPELINE")
        print(f"# Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("#"*70)
        
        # Check environment files
        if not os.path.exists('data-pipeline/.env'):
            print("\nERROR: data-pipeline/.env not found!")
            print("Please create it from .env.example")
            return
        
        if not os.path.exists('data-pipeline/.env.gcp'):
            print("\nERROR: data-pipeline/.env.gcp not found!")
            print("Please create it from .env.gcp.example")
            return
        
        # Step 1: Clean GCP database
        if not self.clean_gcp_database():
            print("⚠ Warning: Failed to clean GCP database, continuing...")
        
        # Step 2: Docker cleanup
        print("\n" + "-"*70)
        print("DOCKER CLEANUP PHASE")
        print("-"*70)
        
        self.run_command_realtime(
            "docker compose down -v",
            "Stop Docker containers and remove volumes"
        )
        
        time.sleep(2)
        
        # Step 3: Docker rebuild with no cache
        print("\n" + "-"*70)
        print("DOCKER REBUILD PHASE")
        print("-"*70)
        
        self.run_command_realtime(
            "docker compose build --no-cache",
            "Rebuild Docker images from scratch (no cache)"
        )
        
        # Step 4: Start Docker
        self.run_command_realtime(
            "docker compose up -d",
            "Start fresh Docker containers"
        )
        
        print("\n⏳ Waiting 15 seconds for PostgreSQL to fully initialize...")
        for i in range(15, 0, -1):
            print(f"   {i} seconds remaining...", end='\r')
            time.sleep(1)
        print("   PostgreSQL ready!          ")
        
        # Step 5: Sync to local Docker
        print("\n" + "-"*70)
        print("LOCAL SYNC PHASE")
        print("-"*70)
        
        self.run_command_realtime(
            "cd data-pipeline && python sync_consolidated_singlefile.py",
            "Sync Airtable → Local Docker PostgreSQL"
        )
        
        # Step 6: Sync to GCP
        print("\n" + "-"*70)
        print("GCP MIGRATION PHASE")
        print("-"*70)
        
        self.run_command_realtime(
            "cd data-pipeline && cp .env.gcp .env && python sync_consolidated_singlefile.py",
            "Migrate Local → GCP Cloud SQL"
        )
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "#"*70)
        print("# PIPELINE COMPLETE")
        print(f"# Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print("# Results Summary:")
        for result in self.results:
            print(f"#   {result}")
        print(f"# Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("#"*70)

if __name__ == "__main__":
    pipeline = PipelineMigration()
    pipeline.run_pipeline()
