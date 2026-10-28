#!/usr/bin/env python3
"""
main.py - FB Auto Pro (Raj FB Pro) CLI Runner Entrypoint
Executes isolated multi-page upload cycles, dry-runs, health audits, and syncs.
"""

import os
import sys
import json
import logging
import argparse
from typing import Optional

from src.config import load_config
from src.db import DatabaseManager
from src.drive_client import GoogleDriveClient
from src.page_runner import process_single_page
from scripts.sync_dashboard_data import sync_all
from scripts.audit_uploads_and_slots import run_audit

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("main")


def load_token_map(tokens_path: str = "data/pages_tokens.json") -> dict:
    if os.path.exists(tokens_path):
        try:
            with open(tokens_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load {tokens_path}: {e}")
    return {}


def main():
    parser = argparse.ArgumentParser(description="FB Auto Pro Automation Engine Runner")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML configuration")
    parser.add_argument("--page-id", default=None, help="Process only a specific Facebook Page ID")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without actual upload or DB changes")
    parser.add_argument("--audit", action="store_true", help="Run health and slot audit and exit")
    parser.add_argument("--sync", action="store_true", help="Run dashboard data sync and exit")
    args = parser.parse_args()

    # If audit requested
    if args.audit:
        run_audit(args.config)
        return

    # If sync requested
    if args.sync:
        sync_all(args.config)
        return

    logger.info("=" * 60)
    logger.info(f"🚀 Starting FB Auto Pro Engine (Dry-Run: {args.dry_run})")
    logger.info("=" * 60)

    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration '{args.config}': {e}")
        sys.exit(1)

    db_manager = DatabaseManager(config.db_path)
    drive_client = GoogleDriveClient(config.service_account_path)
    token_map = load_token_map()

    # Filter target pages
    target_pages = config.pages
    if args.page_id:
        target_pages = [p for p in target_pages if p.page_id == args.page_id]
        if not target_pages:
            logger.error(f"Page ID '{args.page_id}' not found in configuration!")
            sys.exit(1)

    logger.info(f"Target Pages to Process: {len(target_pages)}")

    # Record run in DB
    run_id = None
    if not args.dry_run:
        run_id = db_manager.record_run_start()

    success_count = 0
    failure_count = 0
    errors = []

    for page in target_pages:
        # Determine page access token
        access_token = page.access_token
        if not access_token and page.page_id in token_map:
            access_token = token_map[page.page_id].get("access_token")
        if not access_token:
            access_token = os.environ.get("FB_PAGE_ACCESS_TOKEN", "ENTER_PAGE_TOKEN")

        result = process_single_page(
            page_config=page,
            master_config=config,
            db_manager=db_manager,
            drive_client=drive_client,
            access_token=access_token,
            dry_run=args.dry_run
        )

        if result.success:
            success_count += 1
            logger.info(f"✔ Page {page.page_id} status: {result.message}")
        else:
            failure_count += 1
            errors.append(f"Page {page.page_id}: {result.message}")
            logger.warning(f"✖ Page {page.page_id} failure: {result.message}")

    # Complete run
    status = "success" if failure_count == 0 else "partial_failure"
    err_summary = "; ".join(errors) if errors else None

    if run_id:
        db_manager.record_run_complete(run_id, status=status, pages_processed=success_count, errors=err_summary)

    logger.info("=" * 60)
    logger.info(f"Execution Completed: {success_count} succeeded, {failure_count} failed.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
