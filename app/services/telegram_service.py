"""
Service layer for Telegram messaging.
"""

import logging
from typing import Dict, Any, List

from app.core.telegram_notifier import send_telegram_message, resolve_and_cache_chat_id

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for managing Telegram messaging."""

    def __init__(self):
        self.logger = logger

    async def send_message(self, message: str) -> Dict[str, Any]:
        """Send a message via Telegram."""
        try:
            # Try to resolve and cache chat ID if not already available
            try:
                chat_id = resolve_and_cache_chat_id()
            except Exception as e:
                self.logger.warning(f"Could not resolve chat ID automatically: {e}")
                chat_id = None

            result = send_telegram_message(
                text=message,
                chat_id=str(chat_id) if chat_id else None,
            )

            return {
                "success": True,
                "message": "Telegram message sent successfully",
                "result": result,
            }

        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            raise Exception(f"Failed to send Telegram message: {str(e)}")


# Global service instance
telegram_service = TelegramService()
