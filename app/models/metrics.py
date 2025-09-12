"""
Pydantic models for technical indicators and metrics data.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class CandleData(BaseModel):
    """Model for OHLCV candlestick data."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class TechnicalIndicators(BaseModel):
    """Model for technical analysis indicators."""

    # Price-based indicators
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None

    # Momentum indicators
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None

    # Volatility indicators
    atr_14: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    bollinger_middle: Optional[float] = None

    # Volume indicators
    volume_sma_20: Optional[float] = None
    volume_ratio: Optional[float] = None  # Current volume / Average volume

    # Market context
    price_change_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None
    volatility_7d: Optional[float] = None  # 7-day rolling standard deviation


class OnChainMetrics(BaseModel):
    """Model for Bitcoin on-chain metrics."""

    # Network metrics
    hash_rate: Optional[float] = None  # Terahashes per second
    difficulty: Optional[float] = None
    block_height: Optional[int] = None
    mempool_size: Optional[int] = None  # Number of unconfirmed transactions
    average_block_size: Optional[float] = None  # MB

    # Address activity
    active_addresses: Optional[int] = None
    new_addresses: Optional[int] = None

    # Transaction metrics
    transaction_count_24h: Optional[int] = None
    average_transaction_fee: Optional[float] = None  # USD
    median_transaction_value: Optional[float] = None  # USD

    # Market metrics
    market_cap: Optional[float] = None
    circulating_supply: Optional[float] = None


class RiskMetrics(BaseModel):
    """Model for portfolio risk analysis metrics."""

    # Return metrics
    total_return: Optional[float] = None  # Percentage
    annualized_return: Optional[float] = None  # Percentage
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None

    # Risk metrics
    max_drawdown: Optional[float] = None  # Percentage
    current_drawdown: Optional[float] = None  # Percentage
    volatility: Optional[float] = None  # Standard deviation of returns
    var_95: Optional[float] = None  # Value at Risk (95% confidence)

    # Trading performance
    win_rate: Optional[float] = None  # Percentage of profitable trades
    profit_factor: Optional[float] = None  # Gross profit / Gross loss
    average_win: Optional[float] = None  # Average winning trade
    average_loss: Optional[float] = None  # Average losing trade
    largest_win: Optional[float] = None
    largest_loss: Optional[float] = None

    # Position metrics
    total_trades: Optional[int] = None
    winning_trades: Optional[int] = None
    losing_trades: Optional[int] = None
    average_trade_duration: Optional[float] = None  # Hours


class MarketContext(BaseModel):
    """Model for overall market context and conditions."""

    # Trend analysis
    short_term_trend: Optional[str] = None  # "bullish", "bearish", "neutral"
    medium_term_trend: Optional[str] = None
    long_term_trend: Optional[str] = None

    # Market regime
    market_regime: Optional[str] = None  # "trending", "ranging", "volatile"
    volatility_regime: Optional[str] = None  # "low", "medium", "high"

    # Support and resistance
    support_levels: Optional[List[float]] = None
    resistance_levels: Optional[List[float]] = None
    current_level: Optional[str] = None  # "support", "resistance", "between"

    # Market sentiment (if available)
    fear_greed_index: Optional[int] = None  # 0-100
    sentiment_score: Optional[float] = None  # -1 to 1


class MetricsSnapshot(BaseModel):
    """Complete metrics snapshot for a specific point in time."""

    timestamp: datetime
    current_price: float
    
    # Core metrics
    technical_indicators: TechnicalIndicators
    risk_metrics: Optional[RiskMetrics] = None
    market_context: Optional[MarketContext] = None
    
    # On-chain data (may not be available for every snapshot)
    onchain_metrics: Optional[OnChainMetrics] = None
    
    # Data quality indicators
    data_completeness: float  # 0-1, percentage of metrics successfully calculated
    calculation_errors: Optional[List[str]] = None


class MetricsHistory(BaseModel):
    """Historical collection of metrics snapshots."""

    snapshots: List[MetricsSnapshot]
    start_date: datetime
    end_date: datetime
    total_snapshots: int
    
    # Summary statistics
    average_rsi: Optional[float] = None
    average_atr: Optional[float] = None
    trend_changes: Optional[int] = None
    high_volatility_periods: Optional[int] = None


class MetricsCalculationConfig(BaseModel):
    """Configuration for metrics calculations."""

    # Technical indicator periods
    rsi_period: int = 14
    atr_period: int = 14
    sma_short_period: int = 20
    sma_medium_period: int = 50
    sma_long_period: int = 200
    ema_fast_period: int = 12
    ema_slow_period: int = 26
    macd_signal_period: int = 9
    
    # Bollinger Bands
    bollinger_period: int = 20
    bollinger_std_dev: float = 2.0
    
    # Volume analysis
    volume_sma_period: int = 20
    
    # Risk calculations
    risk_free_rate: float = 0.02  # 2% annual risk-free rate
    var_confidence: float = 0.95  # 95% confidence for VaR
    
    # Data requirements
    min_data_points: int = 200  # Minimum historical data points needed
    max_cache_age_hours: int = 1  # Maximum age for cached calculations


class ATRConfig(BaseModel):
    """Configuration specifically for ATR-based stop-loss calculations."""

    atr_period: int = 14
    atr_multiplier: float = 1.5  # For stop-loss calculation
    atr_multiplier_swing: float = 2.0  # For swing trading stops
    max_stop_loss_percentage: float = 0.1  # 10% maximum stop loss
    min_stop_loss_percentage: float = 0.02  # 2% minimum stop loss