"""
Configuration settings for the BTC Trading Bot application.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    app_name: str = "BTC Trading Bot"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Google Sheets settings
    google_sheet_id: str = "1A58QwxlFcy2zJGfcPRlBLtlaoC7eundbS6DpG24nMao"
    google_worksheet_name: str = "Sheet1"
    google_application_credentials: Optional[str] = None
    gcp_service_account_json: Optional[str] = None
    google_oauth_client_secrets: Optional[str] = None
    google_oauth_token_path: Optional[str] = None

    # Coinbase settings
    coinbase_candles_granularity: str = "30m"

    # Telegram settings
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_chat_username: Optional[str] = None

    # File paths
    config_cache_path: str = "./config_cache.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


# Global settings instance
settings = get_settings()
