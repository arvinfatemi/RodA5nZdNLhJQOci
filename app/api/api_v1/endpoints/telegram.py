"""
API endpoints for Telegram messaging.
"""

from fastapi import APIRouter, HTTPException

from app.models.telegram import TelegramMessageRequest, TelegramMessageResponse
from app.services.telegram_service import telegram_service

router = APIRouter()


@router.post("/telegram/send", response_model=TelegramMessageResponse)
async def send_telegram_message(request: TelegramMessageRequest):
    """Send a message via Telegram."""
    try:
        result = await telegram_service.send_message(request.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
