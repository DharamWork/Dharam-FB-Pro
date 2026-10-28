import pytest
from unittest.mock import MagicMock
from src.config import FacebookPageConfig, MasterConfig
from src.page_runner import process_single_page


def test_page_isolation_failure_does_not_raise():
    # If a page fails, process_single_page should return a failure result object, NOT raise an unhandled exception
    page = FacebookPageConfig(
        page_id="page_fail_123",
        name="isolated_fail",
        display_name="Isolated Failure Test",
        drive_folder_id="bad_folder",
        daily_limit=4,
        enabled=True
    )
    master_cfg = MasterConfig()

    mock_db = MagicMock()
    mock_db.get_daily_upload_count.return_value = 0

    mock_drive = MagicMock()
    mock_drive.is_configured = True
    # Simulate Drive API throwing network error
    mock_drive.get_unposted_videos.side_effect = RuntimeError("Google Drive API rate limit")

    result = process_single_page(
        page_config=page,
        master_config=master_cfg,
        db_manager=mock_db,
        drive_client=mock_drive,
        access_token="fake_token",
        dry_run=False
    )

    assert result.success is False
    assert "Google Drive API rate limit" in result.message
    # Confirms execution gracefully caught the exception and isolated the page
