#!/usr/bin/env python3
"""
src/notifier.py
Zero-Failure, Non-Blocking Telegram Notification Engine.
Sends real-time receipts and alerts when Reels are posted or stock runs low.
If Telegram credentials are not set, it silently skips with zero impact on workflow execution.
"""

import os
import logging
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Non-blocking notifier for Telegram Bot API.
    Designed with a strict 'never-crash' principle:
    Missing tokens, network timeouts, or API errors are logged and safely ignored.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        timeout: int = 10
    ):
        self.bot_token = bot_token.strip() if bot_token is not None else os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = chat_id.strip() if chat_id is not None else os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        self.timeout = timeout

        # Support reading from local .env if not found in os.environ
        if bot_token is None and chat_id is None and (not self.bot_token or not self.chat_id):
            self._load_from_env_file()

    def _load_from_env_file(self):
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("TELEGRAM_BOT_TOKEN=") and not self.bot_token:
                            self.bot_token = line.split("=", 1)[1].strip()
                        elif line.startswith("TELEGRAM_CHAT_ID=") and not self.chat_id:
                            self.chat_id = line.split("=", 1)[1].strip()
            except Exception as e:
                logger.debug(f"Could not parse .env for Telegram credentials: {e}")

    @property
    def is_configured(self) -> bool:
        """Returns True only if both bot_token and chat_id are present."""
        return bool(self.bot_token and self.chat_id and self.bot_token != "ENTER_BOT_TOKEN")

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Sends a text message to the configured Telegram chat.
        Never raises exceptions; returns True on success, False on skip/failure.
        """
        if not self.is_configured:
            logger.info("ℹ️ Telegram notification skipped (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured).")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            data = resp.json()
            if resp.status_code == 200 and data.get("ok"):
                logger.info("✔ Telegram notification delivered successfully.")
                return True
            else:
                desc = data.get("description", "Unknown error")
                logger.warning(f"Telegram API warning (HTTP {resp.status_code}): {desc}")
                return False
        except Exception as e:
            logger.warning(f"Telegram notification non-fatal network error: {e}")
            return False

    def notify_reel_uploaded(
        self,
        page_name: str,
        page_id: str,
        reel_title: str,
        fb_video_id: str,
        stock_remaining: int,
        route: str = "reel"
    ) -> bool:
        """Sends an elegant Telegram receipt after a successful reel upload."""
        fb_link = f"https://www.facebook.com/reel/{fb_video_id}" if route == "reel" else f"https://www.facebook.com/{page_id}/videos/{fb_video_id}"
        
        stock_badge = f"{stock_remaining} videos ready"
        if stock_remaining < 5:
            stock_badge += " ⚠️ *LOW STOCK ALERT*"
        else:
            stock_badge += " ✅ Healthy"

        message = (
            f"🎬 *Dharam FB Pro — Reel Published!*\n\n"
            f"📄 *Page:* `{page_name}`\n"
            f"🎥 *Title:* {reel_title}\n"
            f"⚡ *Format:* `{route.upper()}`\n"
            f"📦 *Drive Stock Left:* {stock_badge}\n"
            f"🔗 *FB Post:* [View on Facebook]({fb_link})\n\n"
            f"🚀 _100% Cloud Runners Synchronized_"
        )
        return self.send_message(message)

    def notify_low_stock(self, page_name: str, stock_remaining: int, drive_folder_id: str) -> bool:
        """Sends a high-priority low-stock warning."""
        drive_link = f"https://drive.google.com/drive/folders/{drive_folder_id}"
        message = (
            f"⚠️ *DHARAM FB PRO — STOCK REFILL ALERT*\n\n"
            f"📄 *Page:* `{page_name}`\n"
            f"📦 *Remaining Videos:* *{stock_remaining}*\n"
            f"💡 *Action Needed:* Refill Google Drive folder to prevent missed posting slots.\n"
            f"📁 *Drive Folder:* [Open Google Drive]({drive_link})"
        )
        return self.send_message(message)

    def notify_error(self, page_name: str, error_message: str) -> bool:
        """Sends a notification if an upload fails on a page."""
        message = (
            f"🚨 *Dharam FB Pro — Upload Warning*\n\n"
            f"📄 *Page:* `{page_name}`\n"
            f"❌ *Error:* `{error_message[:300]}`\n"
            f"ℹ️ _System will retry in next scheduled cloud slot._"
        )
        return self.send_message(message)

