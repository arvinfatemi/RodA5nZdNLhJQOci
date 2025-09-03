"""
Pydantic models for configuration-related data.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ConfigResponse(BaseModel):
    """Response model for configuration data."""
    success: bool
    config: Dict[str, Any]


class ConfigMeta(BaseModel):
    """Configuration metadata model."""
    source: str
    fetched_at_iso: str