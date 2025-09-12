"""
Pydantic models for WebSocket-related data.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel


class WebSocketStartResponse(BaseModel):
    """Response model for WebSocket start operation."""

    success: bool
    message: str


class WebSocketStopResponse(BaseModel):
    """Response model for WebSocket stop operation."""

    success: bool
    message: str


class WebSocketStatusResponse(BaseModel):
    """Response model for WebSocket status."""

    is_running: bool
    latest_data: Dict[str, Optional[Dict[str, Any]]]
