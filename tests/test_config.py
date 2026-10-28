import pytest
from src.config import MasterConfig, FacebookPageConfig, MetaAppConfig, load_config


def test_config_models_default():
    cfg = MasterConfig()
    assert cfg.meta_app.app_mode == "live"
    assert cfg.network.region in ["UK", "USA"]
    assert cfg.max_retries == 3
    assert cfg.db_path == "data/posted_videos.db"


def test_facebook_page_config():
    page = FacebookPageConfig(
        page_id="123456789",
        name="test_page",
        display_name="Test Page Title",
        drive_folder_id="folder_abc_123",
        daily_limit=4,
        enabled=True
    )
    assert page.page_id == "123456789"
    assert page.daily_limit == 4
    assert page.enabled is True


def test_load_config_file():
    cfg = load_config("config.yaml")
    assert cfg is not None
    assert len(cfg.pages) > 0
    assert cfg.meta_app.app_mode == "live"
