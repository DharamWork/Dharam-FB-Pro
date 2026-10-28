import pytest
from src.video_utils import VideoMetadata


def test_reel_routing():
    # Vertical 9:16 and under 90 seconds
    meta = VideoMetadata(duration=45.0, width=1080, height=1920, filename="reel_clip.mp4")
    assert meta.is_vertical is True
    assert meta.route == "reel"


def test_classic_video_duration_over_90s():
    # Vertical but duration > 90 seconds (e.g. 120s) -> classic_video
    meta = VideoMetadata(duration=120.0, width=1080, height=1920, filename="long_video.mp4")
    assert meta.route == "classic_video"


def test_classic_video_horizontal():
    # Horizontal 16:9 even if under 90s -> classic_video
    meta = VideoMetadata(duration=30.0, width=1920, height=1080, filename="horizontal.mp4")
    assert meta.is_vertical is False
    assert meta.route == "classic_video"


def test_short_reel_boundary():
    # 3 seconds minimum boundary
    short = VideoMetadata(duration=2.5, width=1080, height=1920, filename="too_short.mp4")
    assert short.route == "classic_video"

    valid = VideoMetadata(duration=3.1, width=1080, height=1920, filename="valid_short.mp4")
    assert valid.route == "reel"
