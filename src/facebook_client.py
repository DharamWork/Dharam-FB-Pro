import os
import time
import logging
from typing import Dict, Any, Optional
import requests
from src.retry import retry_with_backoff

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v20.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class FacebookClient:
    """Handles publishing Reels & Videos and fetching page insights via Meta Graph API."""

    def __init__(self, page_id: str, access_token: str, timeout: int = 300):
        self.page_id = page_id
        self.access_token = access_token
        self.timeout = timeout

    @retry_with_backoff(retries=3, initial_delay=2.0)
    def verify_token(self) -> Dict[str, Any]:
        """Validates that the page access token is valid and returns page info."""
        url = f"{GRAPH_API_BASE}/{self.page_id}"
        params = {
            "fields": "id,name,fan_count,followers_count,picture.type(large)",
            "access_token": self.access_token
        }
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        if "error" in data:
            raise PermissionError(f"Meta Token validation failed for page {self.page_id}: {data['error'].get('message')}")
        return data

    @retry_with_backoff(retries=3, initial_delay=2.0)
    def get_page_insights(self) -> Dict[str, Any]:
        """Fetches total followers, views, and details for the page."""
        url = f"{GRAPH_API_BASE}/{self.page_id}"
        params = {
            "fields": "id,name,fan_count,followers_count,picture.type(large)",
            "access_token": self.access_token
        }
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        if "error" in data:
            logger.warning(f"Failed to fetch insights for page {self.page_id}: {data['error'].get('message')}")
            return {"followers": 0, "name": self.page_id, "avatar_url": ""}

        followers = data.get("followers_count") or data.get("fan_count") or 0
        name = data.get("name", self.page_id)
        avatar = data.get("picture", {}).get("data", {}).get("url", "")

        return {
            "page_id": self.page_id,
            "name": name,
            "followers": followers,
            "avatar_url": avatar
        }

    def upload_reel(
        self,
        video_path: str,
        description: str = "",
        dry_run: bool = False
    ) -> str:
        """
        Executes the official 3-phase Meta Reels Graph API upload flow:
        Phase 1: Initialize session (POST /{page_id}/video_reels)
        Phase 2: Stream binary chunks to upload_url
        Phase 3: Publish Reel (upload_phase=finish)
        """
        if dry_run:
            logger.info(f"[DRY-RUN] Simulating Reel upload of '{video_path}' to Page {self.page_id}")
            return f"dry_run_reel_{int(time.time())}"

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        file_size = os.path.getsize(video_path)
        logger.info(f"Starting Reel upload to Page {self.page_id} ({file_size / (1024*1024):.2f} MB)...")

        # Phase 1: Initialize
        init_url = f"{GRAPH_API_BASE}/{self.page_id}/video_reels"
        init_payload = {
            "upload_phase": "start",
            "access_token": self.access_token
        }
        init_resp = requests.post(init_url, data=init_payload, timeout=self.timeout)
        init_data = init_resp.json()

        if "error" in init_data:
            raise RuntimeError(f"Reel upload start error: {init_data['error'].get('message')}")

        video_id = init_data["video_id"]
        upload_url = init_data["upload_url"]
        logger.debug(f"Reel session initialized. Video ID: {video_id}")

        # Phase 2: Binary transfer
        with open(video_path, "rb") as video_file:
            headers = {
                "Authorization": f"OAuth {self.access_token}",
                "offset": "0",
                "file_size": str(file_size)
            }
            upload_resp = requests.post(upload_url, headers=headers, data=video_file, timeout=self.timeout)
            upload_data = upload_resp.json()
            if not upload_data.get("success", False):
                raise RuntimeError(f"Reel binary chunk transfer failed: {upload_data}")

        # Phase 3: Publish
        publish_payload = {
            "upload_phase": "finish",
            "access_token": self.access_token,
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": description
        }
        publish_resp = requests.post(init_url, data=publish_payload, timeout=self.timeout)
        publish_data = publish_resp.json()

        if "error" in publish_data:
            raise RuntimeError(f"Reel publish error: {publish_data['error'].get('message')}")

        logger.info(f"Reel published successfully! Facebook Video ID: {video_id}")
        return str(video_id)

    def upload_classic_video(
        self,
        video_path: str,
        title: str = "",
        description: str = "",
        dry_run: bool = False
    ) -> str:
        """
        Uploads classic video (>90 seconds or horizontal) to POST /{page_id}/videos.
        """
        if dry_run:
            logger.info(f"[DRY-RUN] Simulating Classic Video upload of '{video_path}' to Page {self.page_id}")
            return f"dry_run_video_{int(time.time())}"

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        file_size = os.path.getsize(video_path)
        logger.info(f"Starting Classic Video upload to Page {self.page_id} ({file_size / (1024*1024):.2f} MB)...")

        url = f"{GRAPH_API_BASE}/{self.page_id}/videos"

        with open(video_path, "rb") as video_file:
            files = {"source": video_file}
            data = {
                "title": title or os.path.basename(video_path),
                "description": description,
                "access_token": self.access_token
            }
            resp = requests.post(url, data=data, files=files, timeout=self.timeout)
            resp_data = resp.json()

        if "error" in resp_data:
            raise RuntimeError(f"Classic video upload error: {resp_data['error'].get('message')}")

        video_id = resp_data.get("id")
        logger.info(f"Classic video published successfully! Facebook Video ID: {video_id}")
        return str(video_id)
