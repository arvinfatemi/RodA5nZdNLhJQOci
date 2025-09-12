"""
API endpoints for Bitcoin price and candles data.
"""

from fastapi import APIRouter, HTTPException, Query

from app.models.bitcoin import BitcoinPriceResponse, BitcoinCandlesResponse
from app.services.bitcoin_service import bitcoin_service

router = APIRouter()


@router.get("/bitcoin/price", response_model=BitcoinPriceResponse)
async def get_bitcoin_price():
    """Get current Bitcoin price using Coinbase SDK or public API."""
    try:
        result = await bitcoin_service.get_bitcoin_price()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bitcoin/candles", response_model=BitcoinCandlesResponse)
async def get_bitcoin_candles(
    hours: int = Query(
        24, ge=1, le=168, description="Number of hours of candle data (1-168)"
    ),
    granularity: str = Query(
        "ONE_HOUR",
        description="Candle granularity (ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, THIRTY_MINUTE, ONE_HOUR, SIX_HOUR, ONE_DAY)",
    ),
):
    """Get Bitcoin candle data using Coinbase SDK or public API."""
    try:
        result = await bitcoin_service.get_bitcoin_candles(
            hours=hours, granularity=granularity
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
