import os
import io
import logging
from typing import List, Dict, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from src.retry import retry_with_backoff

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]


from google.oauth2.credentials import Credentials as UserCredentials
from google.auth.transport.requests import Request


class GoogleDriveClient:
    """Handles interaction with Google Drive via User Credentials or Service Account API."""

    def __init__(self, service_account_path: str = "service_account.json", token_path: str = "token.json"):
        self.service_account_path = service_account_path
        self.token_path = token_path
        self._service = None

    @property
    def is_configured(self) -> bool:
        """Returns True if user token or service account key file exists."""
        return os.path.exists(self.token_path) or os.path.exists(self.service_account_path) or "GDRIVE_USER_TOKEN_JSON" in os.environ

    def _get_service(self):
        if self._service is not None:
            return self._service

        creds = None

        # 1. First priority: Check Owner User Credentials (token.json or env secret)
        env_token = os.environ.get("GDRIVE_USER_TOKEN_JSON")
        if env_token:
            try:
                import json
                info = json.loads(env_token)
                creds = UserCredentials.from_authorized_user_info(info, SCOPES)
            except Exception as e:
                logger.warning(f"Could not parse GDRIVE_USER_TOKEN_JSON: {e}")

        if not creds and os.path.exists(self.token_path):
            try:
                creds = UserCredentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception as e:
                logger.warning(f"Could not load {self.token_path}: {e}")

        if creds:
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Persist refreshed token
                    with open(self.token_path, "w", encoding="utf-8") as f:
                        f.write(creds.to_json())
                except Exception as ref_err:
                    logger.warning(f"Failed to refresh user token: {ref_err}")
            self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
            return self._service

        # 2. Second priority: Fall back to Service Account key file
        if os.path.exists(self.service_account_path):
            creds = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=SCOPES
            )
            self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
            return self._service

        raise FileNotFoundError(
            f"Neither user token ('{self.token_path}') nor service account ('{self.service_account_path}') found."
        )

    @retry_with_backoff(retries=3, initial_delay=2.0)
    def list_videos_in_folder(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        Lists all video files in a Google Drive folder ordered FIFO (createdTime asc).
        """
        service = self._get_service()
        query = f"'{folder_id}' in parents and mimeType contains 'video/' and trashed = false"

        files = []
        page_token = None

        while True:
            response = service.files().list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, size, createdTime)",
                orderBy="createdTime asc",
                pageToken=page_token,
                pageSize=100
            ).execute()

            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return files

    def get_unposted_videos(self, folder_id: str, db_manager) -> List[Dict[str, Any]]:
        """
        Retrieves all video files from folder and filters out any already posted in DB.
        """
        all_videos = self.list_videos_in_folder(folder_id)
        unposted = [v for v in all_videos if not db_manager.is_video_posted(v["id"])]
        return unposted

    def get_folder_stock_count(self, folder_id: str, db_manager) -> int:
        """
        Returns number of unposted playable videos remaining in the folder.
        """
        if not self.is_configured:
            return 0
        try:
            unposted = self.get_unposted_videos(folder_id, db_manager)
            return len(unposted)
        except Exception as e:
            logger.warning(f"Could not fetch stock for folder {folder_id}: {e}")
            return 0

    @retry_with_backoff(retries=3, initial_delay=3.0)
    def download_file(self, file_id: str, destination_path: str) -> str:
        """
        Downloads a file from Google Drive to destination_path in chunks.
        """
        service = self._get_service()
        request = service.files().get_media(fileId=file_id)

        os.makedirs(os.path.dirname(os.path.abspath(destination_path)), exist_ok=True)
        with open(destination_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=10 * 1024 * 1024)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download {file_id}: {int(status.progress() * 100)}%")

        logger.info(f"File {file_id} successfully downloaded to {destination_path}")
        return destination_path

    def _get_or_create_archive_folder(self, parent_folder_id: str) -> str:
        """Finds or creates a _POSTED_ARCHIVE subfolder inside parent_folder_id."""
        service = self._get_service()
        q = f"'{parent_folder_id}' in parents and name = '_POSTED_ARCHIVE' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res = service.files().list(q=q, fields="files(id)").execute()
        files = res.get("files", [])
        if files:
            return files[0]["id"]

        meta = {
            "name": "_POSTED_ARCHIVE",
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id]
        }
        created = service.files().create(body=meta, fields="id").execute()
        return created["id"]

    @retry_with_backoff(retries=3, initial_delay=2.0)
    def handle_post_upload_cleanup(self, file_id: str, parent_folder_id: str) -> str:
        """
        Handles post-upload cleanup safely:
        1. Attempts permanent deletion.
        2. Attempts moving to Trash.
        3. If Google prevents deletion (ownership restriction), moves file to '_POSTED_ARCHIVE'
           subfolder inside parent_folder_id so it NEVER gets orphaned outside.
        """
        service = self._get_service()

        # Attempt 1: Direct permanent delete
        try:
            service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
            logger.info(f"File {file_id} permanently deleted from Google Drive.")
            return "deleted"
        except Exception as e1:
            logger.debug(f"Direct delete not permitted by Google: {e1}")

        # Attempt 2: Move to Trash
        try:
            service.files().update(fileId=file_id, body={"trashed": True}, supportsAllDrives=True).execute()
            logger.info(f"File {file_id} moved to Google Drive Trash.")
            return "trashed"
        except Exception as e2:
            logger.debug(f"Trash update not permitted by Google: {e2}")

        # Attempt 3: Move to _POSTED_ARCHIVE subfolder (Prevents file from being thrown outside)
        try:
            archive_id = self._get_or_create_archive_folder(parent_folder_id)
            service.files().update(
                fileId=file_id,
                addParents=archive_id,
                removeParents=parent_folder_id,
                fields="id, parents",
                supportsAllDrives=True
            ).execute()
            logger.info(f"File {file_id} safely moved to '_POSTED_ARCHIVE' folder (Zero orphan).")
            return "archived"
        except Exception as e3:
            logger.error(f"Failed to move file {file_id} to archive: {e3}")
            return "failed"
