"""
API endpoints for WebSocket management.
"""

from fastapi import APIRouter, HTTPException

from app.models.websocket import (
    WebSocketStartResponse,
    WebSocketStopResponse,
    WebSocketStatusResponse,
)
from app.services.websocket_service import websocket_service

router = APIRouter()


@router.post("/websocket/start", response_model=WebSocketStartResponse)
async def start_websocket():
    """Start Coinbase WebSocket connection."""
    try:
        result = await websocket_service.start_websocket()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/websocket/stop", response_model=WebSocketStopResponse)
async def stop_websocket():
    """Stop Coinbase WebSocket connection."""
    try:
        result = await websocket_service.stop_websocket()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/websocket/status", response_model=WebSocketStatusResponse)
async def get_websocket_status():
    """Get WebSocket connection status and latest data."""
    try:
        result = await websocket_service.get_websocket_status()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
