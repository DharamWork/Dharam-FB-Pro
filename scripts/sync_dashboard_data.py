#!/usr/bin/env python3
"""
scripts/sync_dashboard_data.py
Synchronizes Meta Graph API insights, Google Drive stock counts,
and SQLite upload history into docs/data/pages_data.json for the PWA dashboard.
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, timedelta, timezone

# Ensure src can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import load_config
from src.db import DatabaseManager
from src.drive_client import GoogleDriveClient
from src.facebook_client import FacebookClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_token_map(tokens_path: str = "data/pages_tokens.json") -> dict:
    env_tokens = os.environ.get("FB_PAGES_TOKENS_JSON")
    if env_tokens:
        try:
            return json.loads(env_tokens)
        except Exception as e:
            logger.warning(f"Could not parse FB_PAGES_TOKENS_JSON from environment: {e}")

    if os.path.exists(tokens_path):
        try:
            with open(tokens_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read tokens from {tokens_path}: {e}")
    return {}


def sync_all(config_path: str = "config.yaml", output_json: str = "docs/data/pages_data.json"):
    logger.info("Starting real-time dashboard data sync...")
    config = load_config(config_path)
    db = DatabaseManager(config.db_path)
    drive_client = GoogleDriveClient(service_account_path=config.service_account_path, token_path="token.json")
    tokens_map = load_token_map()

    total_followers = 0
    total_views = 0
    total_stock = 0

    pages_output = []

    for page in config.pages:
        # Determine token
        token = page.access_token
        if not token and page.page_id in tokens_map:
            token = tokens_map[page.page_id].get("access_token")
        if not token:
            token = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")

        # 1. Drive stock count & Up Next queue preview
        stock = 0
        up_next_list = []
        if drive_client.is_configured:
            try:
                unposted = drive_client.get_unposted_videos(page.drive_folder_id, db)
                stock = len(unposted)
                for item in unposted[:5]:
                    raw_title = item.get("name", "Untitled")
                    base_name, _ = os.path.splitext(raw_title)
                    sz_bytes = int(item.get("size", 0)) if item.get("size") else 0
                    sz_mb = round(sz_bytes / (1024 * 1024), 1) if sz_bytes else 0
                    up_next_list.append({
                        "id": item.get("id"),
                        "title": base_name,
                        "filename": raw_title,
                        "size_mb": sz_mb,
                        "created_time": item.get("createdTime", "")
                    })
            except Exception as e:
                logger.warning(f"Could not fetch unposted videos for folder {page.drive_folder_id}: {e}")
                stock = drive_client.get_folder_stock_count(page.drive_folder_id, db)
        total_stock += stock

        # 2. Meta Insights (Followers & Avatar)
        followers = 0
        avatar_url = f"https://graph.facebook.com/v20.0/{page.page_id}/picture?type=large"
        token_healthy = bool(token and token != "ENTER_PAGE_TOKEN")

        # 3. Real-Time Video Views from Meta Graph API
        page_views = 0
        if token_healthy:
            try:
                fb = FacebookClient(page.page_id, token)
                insights = fb.get_page_insights()
                followers = insights.get("followers", 0)
                if insights.get("avatar_url"):
                    avatar_url = insights["avatar_url"]
            except Exception as e:
                logger.warning(f"Token/Insights issue for page {page.page_id}: {e}")
                token_healthy = False

            try:
                # Query all published videos on this page and sum real views
                v_url = f"https://graph.facebook.com/v20.0/{page.page_id}/videos?fields=views,id,title&access_token={token}"
                v_resp = requests.get(v_url, timeout=15).json()
                video_list = v_resp.get("data", [])
                page_views = sum(int(v.get("views", 0)) for v in video_list)
                logger.info(f"Page {page.display_name} ({page.page_id}): {len(video_list)} videos, real total views: {page_views}")
            except Exception as v_err:
                logger.warning(f"Error fetching real video views for {page.page_id}: {v_err}")
                page_views = 0

        total_followers += followers
        total_views += page_views

        # 4. Database Last Post & Recent stats
        last_posted = db.get_last_posted_time(page.page_id)
        
        # Calculate health status
        is_gap_alert = False
        if last_posted:
            try:
                dt = datetime.strptime(last_posted, "%Y-%m-%d %H:%M:%S")
                if datetime.now(timezone.utc) - dt > timedelta(days=3):
                    is_gap_alert = True
            except Exception:
                pass
        else:
            is_gap_alert = False

        pages_output.append({
            "page_id": page.page_id,
            "name": page.name,
            "display_name": page.display_name,
            "account_group": page.account_group,
            "drive_folder_id": page.drive_folder_id,
            "followers": followers,
            "views": page_views,
            "stock_count": stock,
            "up_next": up_next_list,
            "last_posted_at": last_posted or "No posts yet",
            "avatar_url": avatar_url,
            "token_healthy": token_healthy,
            "gap_alert": is_gap_alert,
            "enabled": page.enabled
        })

    # Recent upload history from DB
    recent_uploads = db.get_recent_uploads(limit=50)

    # Sort performers
    top_performers = sorted(pages_output, key=lambda x: x["views"], reverse=True)
    low_performers = [p for p in pages_output if p["views"] < 500]

    # Generate 7-day upload performance trend for chart
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    daily_analytics = []
    for day_offset in range(6, -1, -1):
        target_date = today - timedelta(days=day_offset)
        date_str = target_date.strftime("%Y-%m-%d")
        day_label = target_date.strftime("%b %d")
        day_count = sum(1 for u in recent_uploads if (u.get("timestamp") or "").startswith(date_str))
        daily_analytics.append({
            "date": date_str,
            "label": day_label,
            "uploads": day_count
        })

    # Calculate Next Scheduled Slot
    slot_defs = [
        {"name": "Slot 1 (Morning)", "est": "09:00 AM EST", "hour": 13, "minute": 0},
        {"name": "Slot 2 (Mid-Day)", "est": "01:00 PM EST", "hour": 17, "minute": 0},
        {"name": "Slot 3 (Evening)", "est": "05:00 PM EST", "hour": 21, "minute": 0},
        {"name": "Slot 4 (Night)", "est": "09:30 PM EST", "hour": 1, "minute": 30, "next_day": True},
    ]

    next_slot_info = None
    min_diff = None

    for slot in slot_defs:
        target_dt = now_utc.replace(hour=slot["hour"], minute=slot["minute"], second=0, microsecond=0)
        if slot.get("next_day") and now_utc.hour >= 2:
            target_dt += timedelta(days=1)
        elif target_dt <= now_utc:
            target_dt += timedelta(days=1)

        diff = (target_dt - now_utc).total_seconds()
        if min_diff is None or diff < min_diff:
            min_diff = diff
            next_slot_info = {
                "name": slot["name"],
                "est": slot["est"],
                "target_iso": target_dt.isoformat(),
                "seconds_left": int(diff)
            }

    payload = {
        "metrics": {
            "total_fleet_followers": total_followers,
            "total_views": total_views,
            "total_reels_published": len(recent_uploads),
            "total_playable_stock": total_stock,
            "last_sync": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "next_slot": next_slot_info
        },
        "daily_analytics": daily_analytics,
        "pages": pages_output,
        "top_performers": top_performers[:50],
        "low_performers": low_performers,
        "recent_uploads": recent_uploads
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Also update telemetry in data/upload_history.json
    history_file = "data/upload_history.json"
    os.makedirs("data", exist_ok=True)
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(recent_uploads, f, indent=2)

    logger.info(f"Dashboard sync complete! Written to '{output_json}' & '{history_file}'.")


if __name__ == "__main__":
    sync_all()
