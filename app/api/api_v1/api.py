"""
API v1 router aggregation.
"""
from fastapi import APIRouter

from app.api.api_v1.endpoints import config, websocket, telegram, bitcoin, trading

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(config.router, tags=["config"])
api_router.include_router(websocket.router, tags=["websocket"]) 
api_router.include_router(telegram.router, tags=["telegram"])
api_router.include_router(bitcoin.router, tags=["bitcoin"])
api_router.include_router(trading.router, tags=["trading"])