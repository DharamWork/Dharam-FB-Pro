import os
import pytest
from unittest.mock import MagicMock, patch
from src.config import FacebookPageConfig, MasterConfig
from src.page_runner import process_single_page


def test_drive_filename_preserved_exact_as_reel_caption():
    """
    Permanent Rule Verification:
    Whatever viral name/hashtags are given in the Google Drive filename,
    MUST be passed 1:1 to Facebook Reel description without alteration.
    """
    raw_drive_filename = "Incredibles 2 💪🙏😂#friendship #pacman #trending #stickman.mp4"
    expected_caption = "Incredibles 2 💪🙏😂#friendship #pacman #trending #stickman"

    page = FacebookPageConfig(
        page_id="1291088570765567",
        name="StickWisdom",
        display_name="StickWisdom",
        drive_folder_id="1jmWnoEkFwYnP3S1KwDJot80BOGHg30Lp",
        daily_limit=4,
        enabled=True
    )
    master_cfg = MasterConfig(auto_delete_from_drive=False)

    mock_db = MagicMock()
    mock_db.get_daily_upload_count.return_value = 0
    mock_db.is_video_posted.return_value = False

    mock_drive = MagicMock()
    mock_drive.is_configured = True
    mock_drive.get_unposted_videos.return_value = [
        {"id": "file_test_999", "name": raw_drive_filename}
    ]

    # Mock probe_video to return a vertical Reel route
    with patch("src.page_runner.probe_video") as mock_probe, \
         patch("src.page_runner.FacebookClient") as mock_fb_class, \
         patch("src.page_runner.tempfile.TemporaryDirectory") as mock_tempdir:

        mock_tempdir.return_value.__enter__.return_value = "/tmp/mock_dir"
        mock_meta = MagicMock()
        mock_meta.route = "reel"
        mock_meta.duration = 25.0
        mock_meta.width = 1080
        mock_meta.height = 1920
        mock_meta.is_vertical = True
        mock_probe.return_value = mock_meta

        mock_fb_instance = MagicMock()
        mock_fb_instance.upload_reel.return_value = "fb_video_999"
        mock_fb_class.return_value = mock_fb_instance

        result = process_single_page(
            page_config=page,
            master_config=master_cfg,
            db_manager=mock_db,
            drive_client=mock_drive,
            access_token="fake_token",
            dry_run=False
        )

        assert result.success is True
        # Verify FacebookClient.upload_reel was called with EXACT cleaned caption
        mock_fb_instance.upload_reel.assert_called_once()
        _, kwargs = mock_fb_instance.upload_reel.call_args
        assert kwargs["description"] == expected_caption
