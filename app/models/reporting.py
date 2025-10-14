"""
Pydantic models for reporting and email reports.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class ReportConfig(BaseModel):
    """Configuration for automated reports."""

    enable_email_reports: bool = True
    report_day: str = "monday"  # monday..sunday
    report_time: str = "09:00"  # HH:MM (24-hour format)
    report_recipient: Optional[str] = None  # Override EMAIL_TO if set


class TradingSummary(BaseModel):
    """Trading activity summary for a period."""

    total_checks: int
    executed_trades: int
    skipped_checks: int
    success_rate: float  # Percentage
    total_invested: float
    average_purchase_price: Optional[float] = None


class PortfolioSummary(BaseModel):
    """Portfolio status summary."""

    total_btc: float
    total_usd_invested: float
    current_btc_value: float  # Current BTC holdings value in USD
    unrealized_pnl: float  # Profit/Loss in USD
    unrealized_pnl_percentage: float  # P&L as percentage
    number_of_purchases: int
    average_entry_price: float


class MarketMetrics(BaseModel):
    """Market performance metrics for a period."""

    period_start_price: float
    period_end_price: float
    price_change: float  # USD
    price_change_percentage: float
    period_high: float
    period_low: float
    average_price: float
    volatility: Optional[float] = None  # Percentage
    average_rsi: Optional[float] = None
    average_volume: Optional[float] = None


class PerformanceMetrics(BaseModel):
    """Performance analysis metrics."""

    best_trade: Optional[Dict[str, Any]] = None  # {date, price, return_pct}
    worst_trade: Optional[Dict[str, Any]] = None
    largest_drawdown: Optional[float] = None  # Percentage
    sharpe_ratio: Optional[float] = None
    total_return: Optional[float] = None  # Percentage
    win_rate: Optional[float] = None  # Percentage (if applicable)


class BotStatus(BaseModel):
    """Bot operational status."""

    is_running: bool
    uptime_days: float
    last_check_time: Optional[datetime] = None
    next_check_time: Optional[datetime] = None
    total_errors: int = 0
    last_error: Optional[str] = None


class WeeklyReportData(BaseModel):
    """Complete data for a weekly report."""

    report_generated_at: datetime
    period_start: datetime
    period_end: datetime
    period_description: str  # e.g., "Jan 6 - Jan 13, 2025"

    trading_summary: TradingSummary
    portfolio_summary: PortfolioSummary
    market_metrics: MarketMetrics
    performance_metrics: PerformanceMetrics
    bot_status: BotStatus

    # Additional context
    notable_events: Optional[List[str]] = None  # e.g., ["Hit ATH", "High volatility period"]
    recommendations: Optional[List[str]] = None  # e.g., ["Consider taking profits"]


class ReportDeliveryStatus(BaseModel):
    """Status of report delivery."""

    success: bool
    report_type: str  # "weekly", "monthly", etc.
    delivered_at: Optional[datetime] = None
    recipient: str
    delivery_method: str  # "email", "telegram", etc.
    error_message: Optional[str] = None
