#!/usr/bin/env python3
# data-pipeline/sync_onefile_runner.py
# NOTE: Full path from project root: data-pipeline/sync_onefile_runner.py
# Purpose: Single-file entry point to run the complete Airtable->PostgreSQL sync
#          (using your latest Ultimate/Final classes) and perform a post-sync
#          verification of per-table and total row counts in schema `airtable_sync`.

import os
import sys
from datetime import datetime

# Ensure local modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your latest, verified implementations
from sync_ultimate import UltimateSyncOrchestrator  # Orchestrator with all fixes/mappings
from airtable_sync import SyncConfig                 # Canonical config (dataclass) with from_env()
import psycopg2

def verify_post_sync_counts(cfg) -> str:
    """
    Connects to PostgreSQL and returns a human-readable report with:
      - Per-table row counts for airtable_sync.*
      - Grand total across all tables
    Mirrors the manual SQL we executed during investigation.
    """
    dsn = {
        "host": cfg.postgres_host,
        "port": cfg.postgres_port,
        "dbname": cfg.postgres_database,
        "user": cfg.postgres_user,
        "password": cfg.postgres_password,
    }
    lines = []
    total = 0
    with psycopg2.connect(**dsn) as conn:
        with conn.cursor() as cur:
            # Per-table counts
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """, (cfg.postgres_schema,))
            tables = [r[0] for r in cur.fetchall()]
            for t in tables:
                cur.execute(f"SELECT COUNT(*) FROM {cfg.postgres_schema}.{t};")
                c = cur.fetchone()[0]
                lines.append(f"  - {t}: {c}")
                total += c
    lines.append(f"\nGrand total rows across schema '{cfg.postgres_schema}': {total}")
    return "\n".join(lines)

def main() -> int:
    # Load .env (AirTable + Postgres vars)
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    except Exception:
        # Proceed even if dotenv is not installed; rely on shell env
        pass

    # Build config from environment (as used by your existing code)
    cfg = SyncConfig.from_env()
    if not cfg.airtable_api_key:
        print("ERROR: AIRTABLE_API_KEY not configured in environment or data-pipeline/.env")
        return 1

    print("\n" + "="*74)
    print(" RICE MARKET — ONE-FILE SYNCHRONIZATION RUNNER")
    print(" Using Ultimate/Final implementations already in your repo")
    print("="*74)
    print(f" Source: Airtable base {cfg.airtable_base_id}")
    print(f" Target: PostgreSQL {cfg.postgres_host}:{cfg.postgres_port} / DB {cfg.postgres_database}")
    print(f" Schema: {cfg.postgres_schema}")
    print(f" Mode:   {cfg.sync_mode.upper()}")
    print("="*74)

    # Run the full sync using your latest orchestrator
    orchestrator = UltimateSyncOrchestrator(cfg)

    start = datetime.now()
    try:
        results = orchestrator.sync_all_tables()
    except Exception as e:
        print(f"\n❌ Fatal sync error: {e}")
        return 1

    # Summarize results from the orchestrator
    succeeded = [r for r in results if r.get("status") == "success"]
    failed    = [r for r in results if r.get("status") == "failed"]

    print("\n--- Synchronization Summary -----------------------------------------")
    print(f" Tables attempted: {len(results)}")
    print(f" Success: {len(succeeded)} | Failed: {len(failed)}")
    if failed:
        for f in failed:
            print(f"   ✗ {f.get('table','?')}: {str(f.get('error','Unknown'))[:120]}")
    tot_processed = sum(r.get("records_processed", 0) for r in succeeded)
    tot_inserted  = sum(r.get("inserted", 0) for r in succeeded)
    tot_updated   = sum(r.get("updated", 0) for r in succeeded)
    elapsed = (datetime.now() - start).total_seconds()
    print(f" Records processed: {tot_processed:,}  (inserted: {tot_inserted:,}, updated: {tot_updated:,})")
    if elapsed > 0:
        print(f" Duration: {elapsed:.1f}s | Throughput: {int(tot_processed/elapsed) if tot_processed else 0} rec/s")

    # Post-sync DB verification (authoritative, from live DB)
    print("\n--- Post-Sync Verification (DB counts) -------------------------------")
    try:
        report = verify_post_sync_counts(cfg)
        print(report)
    except Exception as e:
        print(f"WARNING: Could not run verification counts: {e}")

    print("\nDone.")
    return 0 if not failed else 2

if __name__ == "__main__":
    sys.exit(main())
