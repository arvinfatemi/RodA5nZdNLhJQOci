"""
Pydantic models for Bitcoin-related data.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class BitcoinPriceData(BaseModel):
    """Model for Bitcoin price data."""

    product_id: str
    current_price: Optional[float]
    price_24h_change: Optional[float]
    volume_24h: Optional[float]
    market_cap: Optional[float] = None
    bid: Optional[float]
    ask: Optional[float]
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    open_24h: Optional[float] = None
    last_24h: Optional[float] = None
    timestamp: str
    source: str
    product_info: Optional[Dict[str, Any]] = None


class BitcoinPriceResponse(BaseModel):
    """Response model for Bitcoin price."""

    success: bool
    data: BitcoinPriceData


class BitcoinCandle(BaseModel):
    """Model for a single Bitcoin candle."""

    timestamp: str
    low: float
    high: float
    open: float
    close: float
    volume: float


class BitcoinCandlesData(BaseModel):
    """Model for Bitcoin candles data."""

    product_id: str
    granularity: str
    granularity_seconds: Optional[int] = None
    hours_requested: int
    start_time: str
    end_time: str
    candles_count: int
    source: str
    candles: List[BitcoinCandle]


class BitcoinCandlesResponse(BaseModel):
    """Response model for Bitcoin candles."""

    success: bool
    data: BitcoinCandlesData
