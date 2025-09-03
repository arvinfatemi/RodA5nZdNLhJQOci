"""
Service layer for configuration management.
"""
import logging
from typing import Dict, Any

from app.core.config_loader import read_app_config_from_sheet
from app.config import settings

logger = logging.getLogger(__name__)


class ConfigService:
    """Service for managing application configuration."""
    
    def __init__(self):
        self.logger = logger

    async def fetch_config(self) -> Dict[str, Any]:
        """Fetch configuration from Google Sheets."""
        try:
            config = read_app_config_from_sheet(
                sheet_id=settings.google_sheet_id,
                worksheet_name=settings.google_worksheet_name,
                cache_path=settings.config_cache_path,
                use_cache_if_recent=True,
            )
            
            return {"success": True, "config": config}
            
        except Exception as e:
            self.logger.error(f"Failed to fetch config: {e}")
            raise Exception(f"Failed to fetch configuration: {str(e)}")


# Global service instance
config_service = ConfigService()