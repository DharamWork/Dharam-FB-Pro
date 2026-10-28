#!/usr/bin/env python3
"""
scripts/validate_config.py
Pre-flight configuration validator.
Validates YAML structure, duplicate IDs, and Meta Live Mode compliance.
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import load_config


def validate_config(path: str = "config.yaml") -> bool:
    print(f"[*] Validating configuration file: {path}")

    if not os.path.exists(path):
        print(f"[FAIL] Config file '{path}' does not exist.")
        return False

    try:
        cfg = load_config(path)
    except Exception as e:
        print(f"[FAIL] Configuration parsing or validation error:\n  {e}")
        return False

    has_warnings = False

    # Check Meta App Live Mode
    if cfg.meta_app.app_mode.lower() != "live":
        print("[WARNING] meta_app.app_mode is NOT 'live'! In development mode, Meta suppresses recommendation reach.")
        has_warnings = True
    else:
        print("[PASS] Meta App mode is set to 'live'.")

    # Check Pages list
    if not cfg.pages:
        print("[WARNING] No Facebook pages are configured under 'pages'.")
        has_warnings = True
    else:
        page_ids = set()
        folder_ids = set()

        for idx, page in enumerate(cfg.pages, 1):
            if page.page_id in page_ids:
                print(f"[FAIL] Duplicate page_id found: '{page.page_id}'")
                return False
            page_ids.add(page.page_id)

            if page.drive_folder_id in folder_ids:
                print(f"[WARNING] Duplicate drive_folder_id '{page.drive_folder_id}' used on multiple pages.")
                has_warnings = True
            folder_ids.add(page.drive_folder_id)

            print(f"  [OK] Page #{idx}: {page.display_name} (ID: {page.page_id}, Limit: {page.daily_limit}/day)")

    # Check Service Account file
    if not os.path.exists(cfg.service_account_path):
        print(f"[NOTE] Service account file not yet found at '{cfg.service_account_path}'. (Dry-run mode supported).")
    else:
        print(f"[PASS] Service account file verified at '{cfg.service_account_path}'.")

    # Check SQLite Database path
    print(f"[PASS] Database path configured at: '{cfg.db_path}'")

    print("\n[SUCCESS] Configuration is valid and ready for pipeline execution!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate FB Auto Pro configuration")
    parser.add_argument("config_file", nargs="?", default="config.yaml", help="Path to YAML configuration")
    args = parser.parse_args()

    success = validate_config(args.config_file)
    sys.exit(0 if success else 1)
