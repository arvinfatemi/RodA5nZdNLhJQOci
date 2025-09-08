"""
Pydantic models for trading-related data.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class PurchaseRecord(BaseModel):
    """Model for a single Bitcoin purchase record."""
    timestamp: datetime
    price: float
    amount_usd: float
    amount_btc: float
    exchange: str = "coinbase"
    order_id: Optional[str] = None
    strategy: str = "dca"


class PurchaseHistory(BaseModel):
    """Model for Bitcoin purchase history."""
    purchases: List[PurchaseRecord]
    total_invested: float
    total_btc_acquired: float
    average_purchase_price: float
    last_purchase_price: Optional[float] = None
    last_purchase_timestamp: Optional[datetime] = None


class DCAConfig(BaseModel):
    """Model for Dollar Cost Averaging configuration."""
    purchase_amount_usd: float
    drop_percentage_threshold: float
    min_time_between_purchases_hours: Optional[int] = 24
    max_purchases_per_day: Optional[int] = 1


class TradingDecision(BaseModel):
    """Model for a trading decision."""
    should_buy: bool
    reason: str
    current_price: float
    last_purchase_price: Optional[float]
    price_drop_percentage: Optional[float]
    recommended_amount_usd: Optional[float]
    time_since_last_purchase_hours: Optional[float]


class TradingDecisionResponse(BaseModel):
    """Response model for trading decisions."""
    success: bool
    decision: TradingDecision
    config: DCAConfig
    purchase_history_summary: dict