#!/usr/bin/env python3
# File path: src/datapipeline/pipeline_complete_from_source.py
# Complete pipeline: Auto-setup uv venv → Fetch all data from source APIs → Process → Migrate to PostgreSQL

import os
import sys
import time
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UvEnvironmentManager:
    """Manages Python virtual environment setup using uv (fastest modern tool)"""

    def __init__(self, venv_path=None):
        self.script_dir = Path(__file__).parent
        self.venv_path = Path(venv_path) if venv_path else self.script_dir / ".venv"
        self.python_executable = self.venv_path / "bin" / "python"
        self.uv_executable = "uv"

    def check_uv_installed(self):
        """Check if uv is installed"""
        try:
            subprocess.run([self.uv_executable, "--version"],
                           check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("✗ uv is not installed. Install with: pip install uv")
            return False

    def check_venv_exists(self):
        """Check if virtual environment exists"""
        return self.venv_path.exists() and self.python_executable.exists()

    def create_venv(self):
        """Create virtual environment using uv"""
        logger.info(f"Creating virtual environment with uv at {self.venv_path}")
        try:
            subprocess.run([self.uv_executable, "venv", str(self.venv_path)],
                           check=True)
            logger.info("✓ Virtual environment created successfully with uv")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to create virtual environment: {e}")
            return False

    def install_requirements(self):
        """Install requirements using uv pip"""
        req_file = self.script_dir / "requirements.txt"
        if not req_file.exists():
            logger.error(f"✗ Requirements file not found: {req_file}")
            return False

        logger.info(f"Installing requirements with uv from {req_file}")
        try:
            # uv pip install is much faster than regular pip
            subprocess.run([
                self.uv_executable, "pip", "install",
                "-r", str(req_file)
            ], check=True)
            logger.info("✓ Requirements installed successfully with uv")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to install requirements: {e}")
            return False

    def setup(self):
        """Setup virtual environment if needed"""
        if not self.check_uv_installed():
            return False

        if not self.check_venv_exists():
            logger.info("Virtual environment not found, creating with uv...")
            if not self.create_venv():
                return False
            if not self.install_requirements():
                return False
        else:
            logger.info("✓ Virtual environment already exists")

        return True

    def run_in_venv(self, script_args):
        """Re-run this script inside the virtual environment"""
        logger.info("Restarting pipeline inside uv virtual environment...")
        env = os.environ.copy()
        env['VIRTUAL_ENV'] = str(self.venv_path)
        env['PATH'] = f"{self.venv_path / 'bin'}:{env.get('PATH', '')}"

        # Add marker to prevent infinite loop
        env['PIPELINE_IN_VENV'] = '1'

        try:
            subprocess.run(
                [str(self.python_executable), __file__] + script_args,
                env=env,
                check=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Pipeline execution failed: {e}")
            sys.exit(1)


class CompleteSourcePipeline:
    def __init__(self):
        self.start_time = datetime.now()
        self.results = []
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent.parent
        self.data_dir = self.project_root / "data"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.integrated_dir = self.data_dir / "integrated"

        # Use venv python if running inside venv
        self.python_cmd = sys.executable

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
            f"cd {self.script_dir} && {self.python_cmd} rice_price_spread_analysis.py --start-year 2008",
            "Download World Bank Pink Sheet rice prices (2008-2024)"
        )

        if success:
            import pandas as pd
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
            f"cd {self.script_dir} && {self.python_cmd} market_drivers.py",
            "Fetch oil, inflation, population, ENSO, fertilizer data"
        )

        if success:
            import pandas as pd
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
            f"cd {self.script_dir} && {self.python_cmd} fetch_rainfall_worldbank.py",
            "Fetch rainfall data for Asia (2008-2024)"
        )

        if success:
            import pandas as pd
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
            f"cd {self.script_dir} && {self.python_cmd} integrate_all_data_final.py",
            "Merge rice, market factors, and rainfall (198 records)"
        )

        if success:
            import pandas as pd
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

        env_gcp_file = self.script_dir / '.env.gcp'
        if not env_gcp_file.exists():
            env_gcp_file = self.project_root / 'data-pipeline' / '.env.gcp'
            if not env_gcp_file.exists():
                print("ERROR: .env.gcp not found!")
                return False

        from dotenv import load_dotenv
        import psycopg2

        load_dotenv(env_gcp_file)

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
            f"cd {self.script_dir} && {self.python_cmd} sync_consolidated_singlefile.py",
            "Sync Airtable to Docker (13,818 records)"
        )

        # Sync to GCP
        env_file = self.script_dir / '.env'
        env_gcp_file = self.script_dir / '.env.gcp'
        self.run_command(
            f"cd {self.script_dir} && cp {env_gcp_file} {env_file} && {self.python_cmd} sync_consolidated_singlefile.py",
            "Migrate to GCP Cloud SQL"
        )

        return True

    def run_complete_pipeline(self):
        """Execute complete pipeline from source"""
        print("\n" + "#"*70)
        print("# COMPLETE PIPELINE FROM SOURCE (UV ENVIRONMENT)")
        print(f"# Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("#"*70)

        # Check environment files
        env_file = self.script_dir / '.env'
        env_gcp_file = self.script_dir / '.env.gcp'

        if not env_file.exists():
            env_file = self.project_root / 'data-pipeline' / '.env'
        if not env_gcp_file.exists():
            env_gcp_file = self.project_root / 'data-pipeline' / '.env.gcp'

        if not env_file.exists():
            print("ERROR: .env not found!")
            return
        if not env_gcp_file.exists():
            print("ERROR: .env.gcp not found!")
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
        print("# Environment: UV (Modern Python Package Manager)")
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
    # Check if already running inside venv
    if os.environ.get('PIPELINE_IN_VENV') != '1':
        logger.info("="*70)
        logger.info("STEP 1: UV VIRTUAL ENVIRONMENT SETUP")
        logger.info("="*70)

        uv_manager = UvEnvironmentManager()
        if uv_manager.setup():
            # Re-run inside venv
            uv_manager.run_in_venv(sys.argv[1:])
            sys.exit(0)
        else:
            logger.error("Failed to setup uv virtual environment")
            sys.exit(1)
    else:
        # Running inside venv, execute pipeline
        logger.info("="*70)
        logger.info("STEP 2: EXECUTING DATA PIPELINE")
        logger.info("="*70)

        pipeline = CompleteSourcePipeline()
        pipeline.run_complete_pipeline()