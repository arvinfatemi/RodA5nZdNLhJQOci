"""
Pydantic models for Telegram-related data.
"""

from typing import List, Dict, Any
from pydantic import BaseModel


class TelegramMessageRequest(BaseModel):
    """Request model for sending Telegram messages."""

    message: str


class TelegramMessageResponse(BaseModel):
    """Response model for Telegram message operations."""

    success: bool
    message: str
    result: List[Dict[str, Any]]
