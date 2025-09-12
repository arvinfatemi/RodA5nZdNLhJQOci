"""
Service layer for trading decision making.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.models.trading import (
    PurchaseRecord,
    PurchaseHistory,
    DCAConfig,
    TradingDecision,
)
from app.services.bitcoin_service import bitcoin_service
from app.services.config_service import config_service
from app.services.metrics_calculation_service import metrics_calculation_service
from app.services.onchain_metrics_service import onchain_metrics_service
from app.models.metrics import MetricsSnapshot

logger = logging.getLogger(__name__)


class DecisionMakerService:
    """Service for making trading decisions based on DCA strategy."""

    def __init__(self):
        self.logger = logger
        self._purchase_history: List[PurchaseRecord] = []
        self._cached_config: Optional[DCAConfig] = None
        self._config_cache_time: Optional[datetime] = None
        self._config_cache_duration_minutes = 30
        # Start with empty history for first purchase

    def get_purchase_history(self) -> PurchaseHistory:
        """Get the current purchase history."""
        if not self._purchase_history:
            return PurchaseHistory(
                purchases=[],
                total_invested=0.0,
                total_btc_acquired=0.0,
                average_purchase_price=0.0,
            )

        total_invested = sum(p.amount_usd for p in self._purchase_history)
        total_btc = sum(p.amount_btc for p in self._purchase_history)
        avg_price = total_invested / total_btc if total_btc > 0 else 0.0

        last_purchase = max(self._purchase_history, key=lambda p: p.timestamp)

        return PurchaseHistory(
            purchases=self._purchase_history,
            total_invested=total_invested,
            total_btc_acquired=total_btc,
            average_purchase_price=avg_price,
            last_purchase_price=last_purchase.price,
            last_purchase_timestamp=last_purchase.timestamp,
        )

    def add_purchase_record(self, record: PurchaseRecord):
        """Add a new purchase record to history."""
        self._purchase_history.append(record)
        self.logger.info(
            f"Added purchase record: {record.amount_usd} USD at {record.price}"
        )

    def _extract_dca_config_from_sheet(self, sheet_config: Dict[str, Any]) -> DCAConfig:
        """Extract DCA configuration from Google Sheets config."""
        try:
            purchase_amount = float(sheet_config.get("dca_amount_usd", 100.0))
            drop_threshold = float(sheet_config.get("dca_drop_threshold_percent", 5.0))
            trading_enabled = bool(sheet_config.get("trading_enabled", True))
            max_daily_trades = int(sheet_config.get("max_daily_trades", 10))
            data_fetch_interval = int(sheet_config.get("data_fetch_interval", 30))

            return DCAConfig(
                purchase_amount_usd=purchase_amount,
                drop_percentage_threshold=drop_threshold,
                trading_enabled=trading_enabled,
                max_daily_trades=max_daily_trades,
                data_fetch_interval=data_fetch_interval,
            )
        except (KeyError, ValueError, TypeError) as e:
            self.logger.warning(
                f"Failed to parse DCA config from sheet, using defaults: {e}"
            )
            return DCAConfig(
                purchase_amount_usd=100.0,
                drop_percentage_threshold=5.0,
                trading_enabled=True,
                max_daily_trades=10,
                data_fetch_interval=30,
            )

    def _is_config_cache_valid(self) -> bool:
        """Check if cached config is still valid (within 30 minutes)."""
        if not self._cached_config or not self._config_cache_time:
            return False

        age_minutes = (datetime.now() - self._config_cache_time).total_seconds() / 60
        return age_minutes < self._config_cache_duration_minutes

    async def get_dca_config(self) -> DCAConfig:
        """Get current DCA configuration, fetching from sheet if cache is expired."""
        if self._is_config_cache_valid():
            self.logger.debug("Using cached DCA config")
            return self._cached_config

        try:
            self.logger.info("Fetching DCA config from Google Sheets")
            config_response = await config_service.fetch_config()

            if config_response.get("success"):
                sheet_config = config_response["config"]
                dca_config = self._extract_dca_config_from_sheet(sheet_config)

                self._cached_config = dca_config
                self._config_cache_time = datetime.now()

                self.logger.info(
                    f"Updated DCA config from sheet: ${dca_config.purchase_amount_usd} at {dca_config.drop_percentage_threshold}% drop"
                )
                return dca_config
            else:
                raise Exception("Config fetch was not successful")

        except Exception as e:
            self.logger.error(f"Failed to fetch config from sheet: {e}")

            if self._cached_config:
                self.logger.warning("Using stale cached config due to fetch failure")
                return self._cached_config
            else:
                self.logger.warning(
                    "No cached config available, using fallback defaults"
                )
                return DCAConfig(
                    purchase_amount_usd=100.0,
                    drop_percentage_threshold=5.0,
                    trading_enabled=True,
                    max_daily_trades=10,
                    data_fetch_interval=30,
                )

    async def should_make_purchase(self, current_price: float) -> TradingDecision:
        """Determine if a purchase should be made based on DCA strategy (percentage drop only)."""
        try:
            dca_config = await self.get_dca_config()
            purchase_history = self.get_purchase_history()

            if not purchase_history.purchases:
                return TradingDecision(
                    should_buy=True,
                    reason="First purchase - no history available",
                    current_price=current_price,
                    last_purchase_price=None,
                    price_drop_percentage=None,
                    recommended_amount_usd=dca_config.purchase_amount_usd,
                )

            last_purchase = max(purchase_history.purchases, key=lambda p: p.timestamp)
            price_drop_percentage = (
                (last_purchase.price - current_price) / last_purchase.price
            ) * 100

            if price_drop_percentage >= dca_config.drop_percentage_threshold:
                return TradingDecision(
                    should_buy=True,
                    reason=f"Price dropped {price_drop_percentage:.2f}% (threshold: {dca_config.drop_percentage_threshold}%)",
                    current_price=current_price,
                    last_purchase_price=last_purchase.price,
                    price_drop_percentage=price_drop_percentage,
                    recommended_amount_usd=dca_config.purchase_amount_usd,
                )
            else:
                return TradingDecision(
                    should_buy=False,
                    reason=f"Price drop insufficient ({price_drop_percentage:.2f}% < {dca_config.drop_percentage_threshold}%)",
                    current_price=current_price,
                    last_purchase_price=last_purchase.price,
                    price_drop_percentage=price_drop_percentage,
                    recommended_amount_usd=None,
                )

        except Exception as e:
            self.logger.error(f"Failed to make trading decision: {e}")
            return TradingDecision(
                should_buy=False,
                reason=f"Error making decision: {str(e)}",
                current_price=current_price,
                last_purchase_price=None,
                price_drop_percentage=None,
                recommended_amount_usd=None,
            )

    async def evaluate_current_market(self) -> TradingDecision:
        """Evaluate current market conditions and make trading decision."""
        try:
            price_response = await bitcoin_service.get_bitcoin_price()
            if not price_response["success"]:
                raise Exception("Failed to fetch current Bitcoin price")

            current_price = price_response["data"]["current_price"]
            return await self.should_make_purchase(current_price)

        except Exception as e:
            self.logger.error(f"Failed to evaluate market: {e}")
            return TradingDecision(
                should_buy=False,
                reason=f"Market evaluation failed: {str(e)}",
                current_price=0.0,
                last_purchase_price=None,
                price_drop_percentage=None,
                recommended_amount_usd=None,
            )

    async def evaluate_market_with_metrics(self) -> Dict[str, Any]:
        """Evaluate current market with comprehensive metrics analysis."""
        try:
            # Get basic trading decision
            basic_decision = await self.evaluate_current_market()
            
            # Get comprehensive metrics snapshot
            self.logger.info("Calculating comprehensive market metrics...")
            metrics_snapshot = await metrics_calculation_service.get_metrics_snapshot()
            
            # Get on-chain metrics (async, may be slower)
            try:
                onchain_metrics = await onchain_metrics_service.get_onchain_metrics()
                network_health = await onchain_metrics_service.get_network_health_score()
                fear_greed_index = await onchain_metrics_service.get_fear_greed_index()
            except Exception as e:
                self.logger.warning(f"Failed to fetch on-chain metrics: {e}")
                onchain_metrics = None
                network_health = {"health_score": 50, "status": "unknown"}
                fear_greed_index = None

            # Analyze metrics for additional insights
            market_analysis = self._analyze_metrics_for_trading(
                metrics_snapshot, 
                onchain_metrics, 
                network_health, 
                fear_greed_index
            )

            return {
                "basic_decision": basic_decision,
                "metrics_snapshot": metrics_snapshot,
                "onchain_metrics": onchain_metrics,
                "network_health": network_health,
                "fear_greed_index": fear_greed_index,
                "market_analysis": market_analysis,
                "enhanced_decision": self._enhance_decision_with_metrics(
                    basic_decision, metrics_snapshot, market_analysis
                )
            }

        except Exception as e:
            self.logger.error(f"Failed to evaluate market with metrics: {e}")
            # Fallback to basic decision
            basic_decision = await self.evaluate_current_market()
            return {
                "basic_decision": basic_decision,
                "enhanced_decision": basic_decision,
                "error": str(e)
            }

    def _analyze_metrics_for_trading(
        self, 
        metrics: MetricsSnapshot, 
        onchain: Optional[Any], 
        network_health: Dict, 
        fear_greed: Optional[int]
    ) -> Dict[str, Any]:
        """Analyze metrics to provide trading insights."""
        analysis = {
            "technical_signals": [],
            "risk_factors": [],
            "opportunities": [],
            "overall_sentiment": "neutral"
        }

        # Technical analysis
        if metrics.technical_indicators:
            ti = metrics.technical_indicators
            
            # RSI analysis
            if ti.rsi_14:
                if ti.rsi_14 > 70:
                    analysis["technical_signals"].append("RSI overbought (>70)")
                    analysis["risk_factors"].append("Overbought conditions")
                elif ti.rsi_14 < 30:
                    analysis["technical_signals"].append("RSI oversold (<30)")
                    analysis["opportunities"].append("Oversold conditions")

            # Moving average analysis
            if ti.sma_20 and ti.sma_50 and metrics.current_price:
                if metrics.current_price > ti.sma_20 > ti.sma_50:
                    analysis["technical_signals"].append("Price above short and medium MA")
                elif metrics.current_price < ti.sma_20 < ti.sma_50:
                    analysis["technical_signals"].append("Price below short and medium MA")

            # Volatility analysis
            if ti.atr_14 and metrics.current_price:
                atr_percentage = (ti.atr_14 / metrics.current_price) * 100
                if atr_percentage > 5:
                    analysis["risk_factors"].append("High volatility (ATR > 5%)")
                elif atr_percentage < 2:
                    analysis["opportunities"].append("Low volatility environment")

        # Market context analysis
        if metrics.market_context:
            mc = metrics.market_context
            if mc.short_term_trend == "bearish" and mc.medium_term_trend == "bearish":
                analysis["risk_factors"].append("Short and medium term bearish trends")
            elif mc.short_term_trend == "bullish" and mc.medium_term_trend == "bullish":
                analysis["opportunities"].append("Short and medium term bullish trends")

        # Network health analysis
        if network_health.get("health_score", 50) < 50:
            analysis["risk_factors"].append("Poor network health")
        elif network_health.get("health_score", 50) > 80:
            analysis["opportunities"].append("Strong network health")

        # Fear & Greed analysis
        if fear_greed:
            if fear_greed < 25:
                analysis["opportunities"].append("Extreme fear - potential buying opportunity")
            elif fear_greed > 75:
                analysis["risk_factors"].append("Extreme greed - potential sell signal")

        # Overall sentiment
        risk_count = len(analysis["risk_factors"])
        opportunity_count = len(analysis["opportunities"])
        
        if opportunity_count > risk_count + 1:
            analysis["overall_sentiment"] = "bullish"
        elif risk_count > opportunity_count + 1:
            analysis["overall_sentiment"] = "bearish"
        else:
            analysis["overall_sentiment"] = "neutral"

        return analysis

    def _enhance_decision_with_metrics(
        self, 
        basic_decision: TradingDecision, 
        metrics: MetricsSnapshot, 
        analysis: Dict[str, Any]
    ) -> TradingDecision:
        """Enhance the basic trading decision with metrics insights."""
        # Start with the basic decision
        enhanced_reason = basic_decision.reason
        should_buy = basic_decision.should_buy

        # Add metrics-based modifications
        if basic_decision.should_buy:
            # If basic decision is to buy, check for risk factors
            risk_factors = analysis.get("risk_factors", [])
            
            if "RSI overbought" in str(risk_factors):
                enhanced_reason += " | WARNING: RSI indicates overbought conditions"
            
            if "High volatility" in str(risk_factors):
                enhanced_reason += " | WARNING: High market volatility detected"
            
            if analysis.get("overall_sentiment") == "bearish":
                enhanced_reason += " | CAUTION: Overall market sentiment is bearish"
        
        else:
            # If basic decision is not to buy, check for opportunities
            opportunities = analysis.get("opportunities", [])
            
            if "Extreme fear" in str(opportunities):
                enhanced_reason += " | NOTE: Extreme fear could indicate buying opportunity"
            
            if "Low volatility" in str(opportunities):
                enhanced_reason += " | NOTE: Low volatility environment"

        # Add metrics summary to reason
        if metrics.technical_indicators and metrics.technical_indicators.rsi_14:
            enhanced_reason += f" | RSI: {metrics.technical_indicators.rsi_14:.1f}"
        
        if metrics.technical_indicators and metrics.technical_indicators.atr_14 and metrics.current_price:
            atr_pct = (metrics.technical_indicators.atr_14 / metrics.current_price) * 100
            enhanced_reason += f" | ATR: {atr_pct:.1f}%"

        return TradingDecision(
            should_buy=should_buy,
            reason=enhanced_reason,
            current_price=basic_decision.current_price,
            last_purchase_price=basic_decision.last_purchase_price,
            price_drop_percentage=basic_decision.price_drop_percentage,
            recommended_amount_usd=basic_decision.recommended_amount_usd,
        )


decision_maker_service = DecisionMakerService()
