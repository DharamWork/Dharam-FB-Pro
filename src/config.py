import os
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
import yaml


class MetaAppConfig(BaseModel):
    app_id: str = Field(default="", description="Meta Developer App ID")
    app_secret: str = Field(default="", description="Meta Developer App Secret")
    app_mode: str = Field(default="live", description="Meta App Mode: live or development")
    user_access_token: Optional[str] = Field(default=None, description="Temporary or user token for token exchange")


class FacebookPageConfig(BaseModel):
    page_id: str = Field(..., description="Unique Facebook Page ID")
    name: str = Field(..., description="Slug or short identifier for page")
    display_name: str = Field(..., description="Human-readable title of page")
    account_group: str = Field(default="Default", description="Account/profile group (e.g. UK Profile 1)")
    drive_folder_id: str = Field(..., description="Google Drive Folder ID dedicated to this page")
    daily_limit: int = Field(default=4, description="Max uploads allowed per 24 hour rolling window")
    enabled: bool = Field(default=True, description="Enable or pause automation for this page")
    access_token: Optional[str] = Field(default=None, description="Permanent page access token override")


class NetworkConfig(BaseModel):
    region: str = Field(default="UK", description="Target geo region: UK, USA, etc.")
    wireguard_enabled: bool = Field(default=False, description="Whether to route through WireGuard VPN")
    wireguard_peer_endpoint: Optional[str] = Field(default=None, description="WireGuard peer endpoint IP/host")
    require_regional_ip: bool = Field(default=False, description="Abort if exit IP does not match target country")


class SchedulesConfig(BaseModel):
    slot_1: str = Field(default="09:00 AM", description="First daily posting time slot")
    slot_2: str = Field(default="01:00 PM", description="Second daily posting time slot")
    slot_3: str = Field(default="05:00 PM", description="Third daily posting time slot")
    slot_4: str = Field(default="09:30 PM", description="Fourth daily posting time slot")


class MasterConfig(BaseModel):
    meta_app: MetaAppConfig = Field(default_factory=MetaAppConfig)
    pages: List[FacebookPageConfig] = Field(default_factory=list)
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    schedules: SchedulesConfig = Field(default_factory=SchedulesConfig)
    service_account_path: str = Field(default="service_account.json", description="Path to Google Cloud service account JSON")
    db_path: str = Field(default="data/posted_videos.db", description="Path to SQLite tracking database")
    max_retries: int = Field(default=3, description="Max retries on network/API failure")
    timeout_seconds: int = Field(default=300, description="HTTP request timeout in seconds")
    auto_delete_from_drive: bool = Field(default=True, description="Auto-delete video from Google Drive after successful post")


def load_config(config_path: str = "config.yaml") -> MasterConfig:
    """Loads and validates a YAML configuration file against MasterConfig."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return MasterConfig(**data)
