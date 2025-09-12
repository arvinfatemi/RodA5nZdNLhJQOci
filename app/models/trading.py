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
    trading_enabled: bool = True
    max_daily_trades: int = 10
    data_fetch_interval: int = 30  # minutes


class TradingDecision(BaseModel):
    """Model for a trading decision."""

    should_buy: bool
    reason: str
    current_price: float
    last_purchase_price: Optional[float]
    price_drop_percentage: Optional[float]
    recommended_amount_usd: Optional[float]


class TradingDecisionResponse(BaseModel):
    """Response model for trading decisions."""

    success: bool
    decision: TradingDecision
    config: DCAConfig
    purchase_history_summary: dict


class SimulatedTrade(BaseModel):
    """Model for a simulated trade execution."""

    timestamp: datetime
    decision: TradingDecision
    executed: bool
    reason: str
    daily_trade_count: int


class TradingBotStatus(BaseModel):
    """Model for trading bot status."""

    is_running: bool
    last_check_time: Optional[datetime] = None
    next_check_time: Optional[datetime] = None
    total_checks_today: int = 0
    total_trades_today: int = 0
    last_error: Optional[str] = None
    uptime_seconds: Optional[float] = None
