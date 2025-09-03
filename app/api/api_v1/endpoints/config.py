"""
API endpoints for configuration management.
"""
from fastapi import APIRouter, HTTPException

from app.models.config import ConfigResponse
from app.services.config_service import config_service

router = APIRouter()


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Fetch configuration from Google Sheets."""
    try:
        result = await config_service.fetch_config()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))