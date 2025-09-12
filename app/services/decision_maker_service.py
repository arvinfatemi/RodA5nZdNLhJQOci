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

logger = logging.getLogger(__name__)


class DecisionMakerService:
    """Service for making trading decisions based on DCA strategy."""

    def __init__(self):
        self.logger = logger
        self._purchase_history: List[PurchaseRecord] = []
        self._cached_config: Optional[DCAConfig] = None
        self._config_cache_time: Optional[datetime] = None
        self._config_cache_duration_minutes = 30
        self._initialize_sample_history()

    def _initialize_sample_history(self):
        """Initialize with sample purchase history for testing."""
        sample_purchases = [
            PurchaseRecord(
                timestamp=datetime.now() - timedelta(days=7),
                price=45000.0,
                amount_usd=100.0,
                amount_btc=100.0 / 45000.0,
                strategy="dca",
            ),
            PurchaseRecord(
                timestamp=datetime.now() - timedelta(days=3),
                price=43000.0,
                amount_usd=100.0,
                amount_btc=100.0 / 43000.0,
                strategy="dca",
            ),
        ]
        self._purchase_history = sample_purchases

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

            return DCAConfig(
                purchase_amount_usd=purchase_amount,
                drop_percentage_threshold=drop_threshold,
                trading_enabled=trading_enabled,
                max_daily_trades=max_daily_trades,
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


decision_maker_service = DecisionMakerService()
