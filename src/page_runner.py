import os
import shutil
import tempfile
import logging
from typing import Dict, Any, Optional
from src.config import FacebookPageConfig, MasterConfig
from src.db import DatabaseManager
from src.drive_client import GoogleDriveClient
from src.facebook_client import FacebookClient
from src.video_utils import probe_video

logger = logging.getLogger(__name__)


class PageExecutionResult:
    def __init__(self, page_id: str, success: bool, message: str, video_id: Optional[str] = None):
        self.page_id = page_id
        self.success = success
        self.message = message
        self.video_id = video_id


def process_single_page(
    page_config: FacebookPageConfig,
    master_config: MasterConfig,
    db_manager: DatabaseManager,
    drive_client: GoogleDriveClient,
    access_token: str,
    dry_run: bool = False
) -> PageExecutionResult:
    """
    Executes a single page's upload cycle with strict failure isolation.
    """
    page_id = page_config.page_id
    logger.info(f"--- [Page: {page_config.display_name} ({page_id})] Starting processing ---")

    if not page_config.enabled:
        logger.info(f"Page {page_id} is disabled in config. Skipping.")
        return PageExecutionResult(page_id, True, "Page is disabled")

    # 1. Check daily upload quota
    current_count = db_manager.get_daily_upload_count(page_id, hours=24)
    if current_count >= page_config.daily_limit:
        msg = f"Daily upload quota reached ({current_count}/{page_config.daily_limit}). Skipping."
        logger.info(f"Page {page_id}: {msg}")
        return PageExecutionResult(page_id, True, msg)

    # 2. Check Drive connection and unposted stock
    if not drive_client.is_configured and not dry_run:
        msg = f"Service account key not found at {drive_client.service_account_path}. Cannot download."
        logger.error(msg)
        return PageExecutionResult(page_id, False, msg)

    if dry_run and not drive_client.is_configured:
        logger.info(f"[DRY-RUN] Simulating upload for {page_config.display_name} with simulated video.")
        sim_drive_id = f"sim_file_{page_id}"
        meta_route = "reel"
        fb_id = f"dry_run_fb_reel_{page_id}"
        return PageExecutionResult(page_id, True, f"[DRY-RUN] Simulated upload success as {meta_route}", fb_id)

    temp_dir = None
    file_id = None
    filename = None
    try:
        unposted_videos = drive_client.get_unposted_videos(page_config.drive_folder_id, db_manager)
        if not unposted_videos:
            msg = f"No new unposted videos found in folder '{page_config.drive_folder_id}'."
            logger.info(f"Page {page_id}: {msg}")
            return PageExecutionResult(page_id, True, msg)

        # 3. Take next FIFO video (oldest first)
        target_video = unposted_videos[0]
        file_id = target_video["id"]
        filename = target_video.get("name", f"video_{file_id}.mp4")
        logger.info(f"Next video to post: '{filename}' (Drive ID: {file_id})")

        temp_dir = tempfile.mkdtemp(prefix=f"fb_auto_{page_id}_")
        local_path = os.path.join(temp_dir, filename)

        # 4. Download video
        drive_client.download_file(file_id, local_path)

        # 5. Probe video for aspect ratio and duration
        metadata = probe_video(local_path)
        route = metadata.route
        logger.info(
            f"Video probed: {metadata.duration:.1f}s, {metadata.width}x{metadata.height}, "
            f"Vertical: {metadata.is_vertical} ➔ Route: {route.upper()}"
        )

        # 6. Upload to Meta Graph API
        fb_client = FacebookClient(page_id, access_token=access_token, timeout=master_config.timeout_seconds)

        if route == "reel":
            fb_video_id = fb_client.upload_reel(
                video_path=local_path,
                description=f"#{page_config.name}",
                dry_run=dry_run
            )
        else:
            fb_video_id = fb_client.upload_classic_video(
                video_path=local_path,
                title=filename.rsplit(".", 1)[0],
                description=f"#{page_config.name}",
                dry_run=dry_run
            )

        # 7. Record in SQLite Database
        if not dry_run:
            db_manager.record_upload(
                page_id=page_id,
                drive_file_id=file_id,
                facebook_video_id=fb_video_id,
                filename=filename,
                post_type=route,
                status="posted"
            )

            # 8. Auto-delete from Google Drive (Clean-up post)
            if getattr(master_config, "auto_delete_from_drive", True):
                try:
                    action = drive_client.handle_post_upload_cleanup(file_id, page_config.drive_folder_id)
                    logger.info(f"Post-upload Google Drive cleanup completed ({action}) for '{filename}'.")
                except Exception as del_err:
                    logger.warning(f"Drive cleanup error for {file_id}: {del_err}")

        logger.info(f"Successfully posted video '{filename}' to Page {page_id}! FB ID: {fb_video_id}")
        return PageExecutionResult(page_id, True, f"Uploaded successfully as {route}", fb_video_id)

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing page {page_id}: {error_msg}", exc_info=True)
        if not dry_run and file_id:
            db_manager.record_upload(
                page_id=page_id,
                drive_file_id=file_id,
                facebook_video_id=None,
                filename=filename or "unknown.mp4",
                post_type="unknown",
                status="failed",
                error_message=error_msg
            )
        return PageExecutionResult(page_id, False, error_msg)

    finally:
        # Clean up temporary downloaded file
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

