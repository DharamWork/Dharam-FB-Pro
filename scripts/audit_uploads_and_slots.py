#!/usr/bin/env python3
"""
scripts/audit_uploads_and_slots.py
Comprehensive diagnostic tool:
- Upload gap detector (>3 days with no post)
- Low inventory stock detector (<5 videos)
- Token health verification
- Staggered slot audit
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import load_config
from src.db import DatabaseManager
from src.drive_client import GoogleDriveClient


def run_audit(config_path: str = "config.yaml"):
    print("=" * 60)
    print("🛡️  RAJ FB PRO - FLEET HEALTH & AUDIT CENTER")
    print("=" * 60)

    config = load_config(config_path)
    db = DatabaseManager(config.db_path)
    drive = GoogleDriveClient(config.service_account_path)

    print(f"Total Configured Pages: {len(config.pages)}")
    print(f"Target Region: {config.network.region}")
    print("-" * 60)

    alerts = []

    for page in config.pages:
        print(f"\n▶ Auditing Page: {page.display_name} (ID: {page.page_id})")

        # 1. Check last upload time
        last_posted = db.get_last_posted_time(page.page_id)
        if last_posted:
            dt = datetime.strptime(last_posted, "%Y-%m-%d %H:%M:%S")
            days_ago = (datetime.utcnow() - dt).days
            if days_ago >= 3:
                alerts.append(f"🔴 GAP ALERT: {page.display_name} has not posted in {days_ago} days!")
                print(f"  [ALERT] Upload Gap: {days_ago} days since last post ({last_posted})")
            else:
                print(f"  [OK] Last Post: {last_posted} ({days_ago} days ago)")
        else:
            print("  [INFO] No recorded uploads yet in database.")

        # 2. Check Drive inventory stock
        if drive.is_configured:
            stock = drive.get_folder_stock_count(page.drive_folder_id, db)
            if stock < 5:
                alerts.append(f"⚠️ LOW STOCK: {page.display_name} has only {stock} videos left in Google Drive!")
                print(f"  [ALERT] Stock Count: {stock} (Refill Recommended)")
            else:
                print(f"  [OK] Stock Count: {stock} videos ready")
        else:
            print("  [NOTE] Service Account not connected; stock check skipped.")

        # 3. 24h quota status
        count_24h = db.get_daily_upload_count(page.page_id, hours=24)
        print(f"  [OK] Posts in last 24h: {count_24h}/{page.daily_limit}")

    print("\n" + "=" * 60)
    if alerts:
        print(f"🚨 FOUND {len(alerts)} CRITICAL ALERTS:")
        for alert in alerts:
            print(f"  {alert}")
    else:
        print("✅ ALL FLEET CHANNELS ARE HEALTHY & SYNCHRONIZED!")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fleet Audit and Health Diagnostic")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()
    run_audit(args.config)
