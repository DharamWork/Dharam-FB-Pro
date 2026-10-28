import os
import tempfile
import pytest
from src.db import DatabaseManager


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_posted.db")
    db = DatabaseManager(db_path)
    yield db
    # Cleanup
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


def test_duplicate_guard(temp_db):
    drive_id = "test_drive_file_001"
    assert temp_db.is_video_posted(drive_id) is False

    temp_db.record_upload(
        page_id="page_1",
        drive_file_id=drive_id,
        facebook_video_id="fb_vid_123",
        filename="clip1.mp4",
        post_type="reel",
        status="posted"
    )

    assert temp_db.is_video_posted(drive_id) is True


def test_daily_quota_counter(temp_db):
    page_id = "page_quota_test"
    assert temp_db.get_daily_upload_count(page_id, hours=24) == 0

    for i in range(3):
        temp_db.record_upload(
            page_id=page_id,
            drive_file_id=f"drive_id_{i}",
            facebook_video_id=f"fb_id_{i}",
            filename=f"video_{i}.mp4",
            post_type="reel",
            status="posted"
        )

    assert temp_db.get_daily_upload_count(page_id, hours=24) == 3


def test_failed_upload_not_counted_in_quota(temp_db):
    page_id = "page_fail_test"
    temp_db.record_upload(
        page_id=page_id,
        drive_file_id="failed_drive_id",
        facebook_video_id=None,
        filename="corrupted.mp4",
        post_type="reel",
        status="failed",
        error_message="Meta API error"
    )

    # Failed uploads should not count towards successful daily limit
    assert temp_db.get_daily_upload_count(page_id, hours=24) == 0
    # And is_video_posted for 'posted' status is False
    assert temp_db.is_video_posted("failed_drive_id") is False
