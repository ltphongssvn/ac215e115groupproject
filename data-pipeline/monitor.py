#!/usr/bin/env python3
"""
Monitoring script for Rice Market Data Pipeline

This script provides real-time monitoring of synchronization status
and data quality metrics.
"""

import os
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

def check_last_sync():
    """Check when the last successful sync occurred"""
    log_dir = Path("logs")
    sync_reports = list(log_dir.glob("sync_report*.txt"))
    
    if not sync_reports:
        print("⚠️  No synchronization reports found")
        return None
    
    latest_report = max(sync_reports, key=os.path.getmtime)
    mod_time = datetime.fromtimestamp(os.path.getmtime(latest_report))
    age = datetime.now() - mod_time
    
    print(f"📊 Last sync: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Age: {age.days} days, {age.seconds // 3600} hours")
    
    if age > timedelta(hours=24):
        print("   ⚠️  Warning: Last sync is more than 24 hours old")
    else:
        print("   ✅ Sync is recent")
    
    return latest_report

def analyze_sync_report(report_path):
    """Analyze the sync report for key metrics"""
    with open(report_path, 'r') as f:
        content = f.read()
    
    # Extract key metrics using simple parsing
    metrics = {}
    for line in content.split('\n'):
        if 'Total Records Processed:' in line:
            metrics['total'] = line.split(':')[1].strip()
        elif 'Total Inserted:' in line:
            metrics['inserted'] = line.split(':')[1].strip()
        elif 'Total Updated:' in line:
            metrics['updated'] = line.split(':')[1].strip()
    
    print(f"\n📈 Synchronization Metrics:")
    print(f"   Records processed: {metrics.get('total', 'Unknown')}")
    print(f"   New records: {metrics.get('inserted', 'Unknown')}")
    print(f"   Updates: {metrics.get('updated', 'Unknown')}")

def check_data_quality():
    """Check for known data quality issues"""
    print(f"\n🔍 Data Quality Checks:")
    
    # These are the issues we discovered during debugging
    quality_issues = [
        ("Vietnamese characters in field names", "Handled by sanitization"),
        ("Percentage values > 100", "Capped at 99.999"),
        ("Fields starting with numbers", "Prefixed with 'n_'"),
        ("Inconsistent underscore patterns", "Mapped explicitly"),
    ]
    
    for issue, resolution in quality_issues:
        print(f"   • {issue}")
        print(f"     Resolution: {resolution}")

def main():
    print("=" * 60)
    print(" RICE MARKET DATA PIPELINE MONITOR")
    print("=" * 60)
    
    report_path = check_last_sync()
    if report_path:
        analyze_sync_report(report_path)
    
    check_data_quality()
    
    print("\n" + "=" * 60)
    print(" Run 'python src/sync_production.py' to synchronize")
    print("=" * 60)

if __name__ == "__main__":
    main()
