"""
Service for calculating technical indicators and advanced metrics.
"""

import logging
import math
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import deque

from app.models.metrics import (
    CandleData,
    TechnicalIndicators,
    OnChainMetrics,
    RiskMetrics,
    MarketContext,
    MetricsSnapshot,
    MetricsCalculationConfig,
    ATRConfig,
)
from app.services.bitcoin_service import bitcoin_service

logger = logging.getLogger(__name__)


class MetricsCalculationService:
    """Service for calculating technical indicators and market metrics."""

    def __init__(self, config: Optional[MetricsCalculationConfig] = None):
        self.logger = logger
        self.config = config or MetricsCalculationConfig()
        
        # Cache for historical data and calculations
        self._price_history: deque = deque(maxlen=1000)  # Keep last 1000 data points
        self._volume_history: deque = deque(maxlen=1000)
        self._candle_history: deque = deque(maxlen=1000)
        
        # Cached indicators to avoid recalculation
        self._indicator_cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None

    # ===========================================
    # TECHNICAL INDICATOR CALCULATIONS
    # ===========================================

    def calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period

    def calculate_ema(self, prices: List[float], period: int, previous_ema: Optional[float] = None) -> Optional[float]:
        """Calculate Exponential Moving Average."""
        if len(prices) == 0:
            return None
        
        current_price = prices[-1]
        
        if previous_ema is None:
            # Initialize with SMA for the first calculation
            if len(prices) < period:
                return None
            return self.calculate_sma(prices[:period], period)
        
        # EMA calculation: EMA = (Current Price * α) + (Previous EMA * (1-α))
        # where α = 2 / (period + 1)
        alpha = 2.0 / (period + 1)
        return (current_price * alpha) + (previous_ema * (1 - alpha))

    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return None

        # Calculate price changes
        changes = []
        for i in range(1, len(prices)):
            changes.append(prices[i] - prices[i - 1])

        # Separate gains and losses
        gains = [change if change > 0 else 0 for change in changes]
        losses = [-change if change < 0 else 0 for change in changes]

        # Calculate average gain and loss over the period
        if len(gains) < period or len(losses) < period:
            return None

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0  # RSI = 100 when there are no losses

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(prices) < slow_period:
            return None, None, None

        # Calculate EMAs
        ema_fast = self.calculate_ema(prices, fast_period)
        ema_slow = self.calculate_ema(prices, slow_period)

        if ema_fast is None or ema_slow is None:
            return None, None, None

        # MACD Line = EMA(12) - EMA(26)
        macd_line = ema_fast - ema_slow

        # For signal line, we need historical MACD values
        # Simplified implementation - in production, you'd maintain MACD history
        macd_signal = None  # Would need historical MACD values to calculate properly
        macd_histogram = None

        return macd_line, macd_signal, macd_histogram

    def calculate_atr(self, candles: List[CandleData], period: int = 14) -> Optional[float]:
        """Calculate Average True Range."""
        if len(candles) < period + 1:
            return None

        true_ranges = []
        for i in range(1, len(candles)):
            current = candles[i]
            previous = candles[i - 1]
            
            # True Range = max(High - Low, |High - Previous Close|, |Low - Previous Close|)
            tr = max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close)
            )
            true_ranges.append(tr)

        if len(true_ranges) < period:
            return None

        # ATR is the average of the true ranges
        return sum(true_ranges[-period:]) / period

    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate Bollinger Bands (Upper, Middle, Lower)."""
        if len(prices) < period:
            return None, None, None

        sma = self.calculate_sma(prices, period)
        if sma is None:
            return None, None, None

        # Calculate standard deviation
        recent_prices = prices[-period:]
        variance = sum((price - sma) ** 2 for price in recent_prices) / period
        std = math.sqrt(variance)

        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)

        return upper_band, sma, lower_band

    # ===========================================
    # RISK METRICS CALCULATIONS
    # ===========================================

    def calculate_returns(self, prices: List[float]) -> List[float]:
        """Calculate price returns."""
        if len(prices) < 2:
            return []
        
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        return returns

    def calculate_volatility(self, returns: List[float]) -> Optional[float]:
        """Calculate volatility (standard deviation of returns)."""
        if len(returns) < 2:
            return None
        return statistics.stdev(returns)

    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> Optional[float]:
        """Calculate Sharpe Ratio."""
        if len(returns) < 2:
            return None
        
        avg_return = statistics.mean(returns)
        volatility = self.calculate_volatility(returns)
        
        if volatility is None or volatility == 0:
            return None
        
        # Annualized Sharpe ratio
        excess_return = avg_return - (risk_free_rate / 252)  # Daily risk-free rate
        return (excess_return * math.sqrt(252)) / (volatility * math.sqrt(252))

    def calculate_max_drawdown(self, prices: List[float]) -> Tuple[Optional[float], Optional[float]]:
        """Calculate maximum drawdown and current drawdown."""
        if len(prices) < 2:
            return None, None

        peak = prices[0]
        max_drawdown = 0.0
        current_drawdown = 0.0

        for price in prices:
            if price > peak:
                peak = price
            
            drawdown = (peak - price) / peak
            max_drawdown = max(max_drawdown, drawdown)
            
        # Current drawdown
        current_peak = max(prices)
        current_price = prices[-1]
        current_drawdown = (current_peak - current_price) / current_peak if current_peak > 0 else 0

        return max_drawdown, current_drawdown

    def calculate_var_95(self, returns: List[float]) -> Optional[float]:
        """Calculate Value at Risk at 95% confidence level."""
        if len(returns) < 20:  # Need sufficient data
            return None
        
        sorted_returns = sorted(returns)
        var_index = int(0.05 * len(sorted_returns))  # 5% tail for 95% VaR
        return abs(sorted_returns[var_index])  # Return as positive value

    # ===========================================
    # MARKET CONTEXT ANALYSIS
    # ===========================================

    def analyze_trend(self, prices: List[float], short_period: int = 20, medium_period: int = 50, long_period: int = 200) -> Dict[str, str]:
        """Analyze market trends across different timeframes."""
        trends = {
            "short_term": "neutral",
            "medium_term": "neutral", 
            "long_term": "neutral"
        }

        if len(prices) < long_period:
            return trends

        current_price = prices[-1]
        
        # Short-term trend
        if len(prices) >= short_period:
            sma_short = self.calculate_sma(prices, short_period)
            if sma_short:
                trends["short_term"] = "bullish" if current_price > sma_short else "bearish"

        # Medium-term trend
        if len(prices) >= medium_period:
            sma_medium = self.calculate_sma(prices, medium_period)
            if sma_medium:
                trends["medium_term"] = "bullish" if current_price > sma_medium else "bearish"

        # Long-term trend
        if len(prices) >= long_period:
            sma_long = self.calculate_sma(prices, long_period)
            if sma_long:
                trends["long_term"] = "bullish" if current_price > sma_long else "bearish"

        return trends

    def detect_market_regime(self, prices: List[float], atr: Optional[float]) -> str:
        """Detect current market regime (trending, ranging, volatile)."""
        if len(prices) < 50 or atr is None:
            return "unknown"

        # Calculate recent price range
        recent_prices = prices[-20:]
        price_range = max(recent_prices) - min(recent_prices)
        avg_price = sum(recent_prices) / len(recent_prices)
        range_percentage = price_range / avg_price

        # Use ATR to determine volatility
        current_price = prices[-1]
        atr_percentage = atr / current_price

        if atr_percentage > 0.05:  # High volatility threshold
            return "volatile"
        elif range_percentage < 0.02:  # Low range threshold
            return "ranging"
        else:
            return "trending"

    def identify_support_resistance(self, candles: List[CandleData], lookback: int = 50) -> Tuple[List[float], List[float]]:
        """Identify support and resistance levels."""
        if len(candles) < lookback:
            return [], []

        recent_candles = candles[-lookback:]
        highs = [candle.high for candle in recent_candles]
        lows = [candle.low for candle in recent_candles]

        # Simple support/resistance detection
        # Find local maxima and minima
        resistance_levels = []
        support_levels = []

        for i in range(2, len(recent_candles) - 2):
            # Resistance: local high
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and 
                highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                resistance_levels.append(highs[i])
            
            # Support: local low
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and 
                lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                support_levels.append(lows[i])

        # Sort and return most significant levels
        resistance_levels.sort(reverse=True)
        support_levels.sort()

        return support_levels[-5:], resistance_levels[-5:]  # Top 5 levels

    # ===========================================
    # MAIN CALCULATION METHODS
    # ===========================================

    async def calculate_technical_indicators(self, candles: List[CandleData]) -> TechnicalIndicators:
        """Calculate all technical indicators from candlestick data."""
        if not candles:
            return TechnicalIndicators()

        prices = [candle.close for candle in candles]
        volumes = [candle.volume for candle in candles]

        # Calculate moving averages
        sma_20 = self.calculate_sma(prices, self.config.sma_short_period)
        sma_50 = self.calculate_sma(prices, self.config.sma_medium_period)
        sma_200 = self.calculate_sma(prices, self.config.sma_long_period)
        ema_12 = self.calculate_ema(prices, self.config.ema_fast_period)
        ema_26 = self.calculate_ema(prices, self.config.ema_slow_period)

        # Calculate momentum indicators
        rsi_14 = self.calculate_rsi(prices, self.config.rsi_period)
        macd_line, macd_signal, macd_histogram = self.calculate_macd(prices)

        # Calculate volatility indicators
        atr_14 = self.calculate_atr(candles, self.config.atr_period)
        bollinger_upper, bollinger_middle, bollinger_lower = self.calculate_bollinger_bands(
            prices, self.config.bollinger_period, self.config.bollinger_std_dev
        )

        # Calculate volume indicators
        volume_sma_20 = self.calculate_sma(volumes, self.config.volume_sma_period)
        volume_ratio = None
        if volume_sma_20 and volumes:
            volume_ratio = volumes[-1] / volume_sma_20

        # Calculate price changes
        price_change_24h = None
        price_change_percentage_24h = None
        if len(prices) >= 2:
            price_change_24h = prices[-1] - prices[-2]
            price_change_percentage_24h = (price_change_24h / prices[-2]) * 100

        # Calculate volatility
        volatility_7d = None
        if len(prices) >= 7:
            recent_returns = self.calculate_returns(prices[-7:])
            volatility_7d = self.calculate_volatility(recent_returns)

        return TechnicalIndicators(
            sma_20=sma_20,
            sma_50=sma_50,
            sma_200=sma_200,
            ema_12=ema_12,
            ema_26=ema_26,
            rsi_14=rsi_14,
            macd_line=macd_line,
            macd_signal=macd_signal,
            macd_histogram=macd_histogram,
            atr_14=atr_14,
            bollinger_upper=bollinger_upper,
            bollinger_lower=bollinger_lower,
            bollinger_middle=bollinger_middle,
            volume_sma_20=volume_sma_20,
            volume_ratio=volume_ratio,
            price_change_24h=price_change_24h,
            price_change_percentage_24h=price_change_percentage_24h,
            volatility_7d=volatility_7d,
        )

    async def calculate_risk_metrics(self, prices: List[float], trade_history: Optional[List] = None) -> RiskMetrics:
        """Calculate portfolio risk metrics."""
        if len(prices) < 2:
            return RiskMetrics()

        returns = self.calculate_returns(prices)
        
        # Basic return calculations
        total_return = ((prices[-1] - prices[0]) / prices[0]) * 100 if prices[0] != 0 else 0
        
        # Risk metrics
        volatility = self.calculate_volatility(returns)
        sharpe_ratio = self.calculate_sharpe_ratio(returns, self.config.risk_free_rate)
        max_drawdown, current_drawdown = self.calculate_max_drawdown(prices)
        var_95 = self.calculate_var_95(returns)

        # Convert to percentages
        max_drawdown_pct = max_drawdown * 100 if max_drawdown else None
        current_drawdown_pct = current_drawdown * 100 if current_drawdown else None
        volatility_pct = volatility * 100 if volatility else None

        return RiskMetrics(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown_pct,
            current_drawdown=current_drawdown_pct,
            volatility=volatility_pct,
            var_95=var_95,
        )

    async def analyze_market_context(self, candles: List[CandleData]) -> MarketContext:
        """Analyze overall market context and conditions."""
        if not candles:
            return MarketContext()

        prices = [candle.close for candle in candles]
        
        # Trend analysis
        trends = self.analyze_trend(prices)
        
        # Market regime detection
        atr = self.calculate_atr(candles, 14)
        market_regime = self.detect_market_regime(prices, atr)
        
        # Volatility regime
        volatility_regime = "medium"
        if atr and prices:
            atr_percentage = atr / prices[-1]
            if atr_percentage > 0.05:
                volatility_regime = "high"
            elif atr_percentage < 0.02:
                volatility_regime = "low"

        # Support and resistance levels
        support_levels, resistance_levels = self.identify_support_resistance(candles)

        return MarketContext(
            short_term_trend=trends["short_term"],
            medium_term_trend=trends["medium_term"],
            long_term_trend=trends["long_term"],
            market_regime=market_regime,
            volatility_regime=volatility_regime,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
        )

    async def get_metrics_snapshot(self) -> MetricsSnapshot:
        """Get a complete metrics snapshot for current market conditions."""
        try:
            # Fetch current price and historical data
            price_response = await bitcoin_service.get_bitcoin_price()
            if not price_response["success"]:
                raise Exception("Failed to fetch current price")
            
            current_price = price_response["data"]["current_price"]
            
            # Fetch historical candle data
            candles_response = await bitcoin_service.get_bitcoin_candles(hours=24*7, granularity="ONE_HOUR")  # 1 week of hourly data
            if not candles_response["success"]:
                raise Exception("Failed to fetch candle data")
            
            # Convert to CandleData objects
            candles_data = []
            for candle in candles_response["data"]["candles"]:
                candles_data.append(CandleData(
                    timestamp=datetime.fromisoformat(candle["timestamp"].replace("Z", "")),
                    open=candle["open"],
                    high=candle["high"],
                    low=candle["low"],
                    close=candle["close"],
                    volume=candle["volume"]
                ))
            
            # Calculate all metrics
            technical_indicators = await self.calculate_technical_indicators(candles_data)
            
            prices = [candle.close for candle in candles_data]
            risk_metrics = await self.calculate_risk_metrics(prices)
            market_context = await self.analyze_market_context(candles_data)
            
            # Calculate data completeness
            indicator_fields = [f for f in technical_indicators.__dict__ if technical_indicators.__dict__[f] is not None]
            total_fields = len(technical_indicators.__dict__)
            data_completeness = len(indicator_fields) / total_fields if total_fields > 0 else 0

            return MetricsSnapshot(
                timestamp=datetime.now(),
                current_price=current_price,
                technical_indicators=technical_indicators,
                risk_metrics=risk_metrics,
                market_context=market_context,
                data_completeness=data_completeness,
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate metrics snapshot: {e}")
            # Return minimal snapshot with error info
            return MetricsSnapshot(
                timestamp=datetime.now(),
                current_price=0.0,
                technical_indicators=TechnicalIndicators(),
                data_completeness=0.0,
                calculation_errors=[str(e)]
            )

    def calculate_atr_stop_loss(self, entry_price: float, atr: float, config: ATRConfig) -> Tuple[float, float]:
        """Calculate ATR-based stop loss levels."""
        stop_loss_distance = atr * config.atr_multiplier
        stop_loss_price = entry_price - stop_loss_distance
        stop_loss_percentage = (stop_loss_distance / entry_price) * 100

        # Apply min/max constraints
        max_stop_distance = entry_price * config.max_stop_loss_percentage
        min_stop_distance = entry_price * config.min_stop_loss_percentage

        if stop_loss_distance > max_stop_distance:
            stop_loss_price = entry_price - max_stop_distance
            stop_loss_percentage = config.max_stop_loss_percentage * 100
        elif stop_loss_distance < min_stop_distance:
            stop_loss_price = entry_price - min_stop_distance
            stop_loss_percentage = config.min_stop_loss_percentage * 100

        return stop_loss_price, stop_loss_percentage


# Global service instance
metrics_calculation_service = MetricsCalculationService()