"""
Service layer for trading decision making.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from app.models.trading import (
    PurchaseRecord, PurchaseHistory, DCAConfig, TradingDecision
)
from app.services.bitcoin_service import bitcoin_service

logger = logging.getLogger(__name__)


class DecisionMakerService:
    """Service for making trading decisions based on DCA strategy."""
    
    def __init__(self):
        self.logger = logger
        self._purchase_history: List[PurchaseRecord] = []
        self._dca_config = DCAConfig(
            purchase_amount_usd=100.0,
            drop_percentage_threshold=5.0,
            min_time_between_purchases_hours=24,
            max_purchases_per_day=1
        )
        self._initialize_sample_history()
    
    def _initialize_sample_history(self):
        """Initialize with sample purchase history for testing."""
        sample_purchases = [
            PurchaseRecord(
                timestamp=datetime.now() - timedelta(days=7),
                price=45000.0,
                amount_usd=100.0,
                amount_btc=100.0 / 45000.0,
                strategy="dca"
            ),
            PurchaseRecord(
                timestamp=datetime.now() - timedelta(days=3),
                price=43000.0,
                amount_usd=100.0,
                amount_btc=100.0 / 43000.0,
                strategy="dca"
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
                average_purchase_price=0.0
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
            last_purchase_timestamp=last_purchase.timestamp
        )
    
    def add_purchase_record(self, record: PurchaseRecord):
        """Add a new purchase record to history."""
        self._purchase_history.append(record)
        self.logger.info(f"Added purchase record: {record.amount_usd} USD at {record.price}")
    
    def get_dca_config(self) -> DCAConfig:
        """Get current DCA configuration."""
        return self._dca_config
    
    def update_dca_config(self, config: DCAConfig):
        """Update DCA configuration."""
        self._dca_config = config
        self.logger.info(f"Updated DCA config: ${config.purchase_amount_usd} at {config.drop_percentage_threshold}% drop")
    
    async def should_make_purchase(self, current_price: float) -> TradingDecision:
        """Determine if a purchase should be made based on DCA strategy."""
        try:
            dca_config = self._dca_config
            purchase_history = self.get_purchase_history()
            
            if not purchase_history.purchases:
                return TradingDecision(
                    should_buy=True,
                    reason="First purchase - no history available",
                    current_price=current_price,
                    last_purchase_price=None,
                    price_drop_percentage=None,
                    recommended_amount_usd=dca_config.purchase_amount_usd,
                    time_since_last_purchase_hours=None
                )
            
            last_purchase = max(purchase_history.purchases, key=lambda p: p.timestamp)
            time_since_last = datetime.now() - last_purchase.timestamp
            time_since_last_hours = time_since_last.total_seconds() / 3600
            
            if time_since_last_hours < dca_config.min_time_between_purchases_hours:
                return TradingDecision(
                    should_buy=False,
                    reason=f"Too soon since last purchase ({time_since_last_hours:.1f}h < {dca_config.min_time_between_purchases_hours}h)",
                    current_price=current_price,
                    last_purchase_price=last_purchase.price,
                    price_drop_percentage=None,
                    recommended_amount_usd=None,
                    time_since_last_purchase_hours=time_since_last_hours
                )
            
            purchases_today = [
                p for p in purchase_history.purchases 
                if p.timestamp.date() == datetime.now().date()
            ]
            
            if len(purchases_today) >= dca_config.max_purchases_per_day:
                return TradingDecision(
                    should_buy=False,
                    reason=f"Daily purchase limit reached ({len(purchases_today)}/{dca_config.max_purchases_per_day})",
                    current_price=current_price,
                    last_purchase_price=last_purchase.price,
                    price_drop_percentage=None,
                    recommended_amount_usd=None,
                    time_since_last_purchase_hours=time_since_last_hours
                )
            
            price_drop_percentage = ((last_purchase.price - current_price) / last_purchase.price) * 100
            
            if price_drop_percentage >= dca_config.drop_percentage_threshold:
                return TradingDecision(
                    should_buy=True,
                    reason=f"Price dropped {price_drop_percentage:.2f}% (threshold: {dca_config.drop_percentage_threshold}%)",
                    current_price=current_price,
                    last_purchase_price=last_purchase.price,
                    price_drop_percentage=price_drop_percentage,
                    recommended_amount_usd=dca_config.purchase_amount_usd,
                    time_since_last_purchase_hours=time_since_last_hours
                )
            else:
                return TradingDecision(
                    should_buy=False,
                    reason=f"Price drop insufficient ({price_drop_percentage:.2f}% < {dca_config.drop_percentage_threshold}%)",
                    current_price=current_price,
                    last_purchase_price=last_purchase.price,
                    price_drop_percentage=price_drop_percentage,
                    recommended_amount_usd=None,
                    time_since_last_purchase_hours=time_since_last_hours
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
                time_since_last_purchase_hours=None
            )
    
    async def evaluate_current_market(self) -> TradingDecision:
        """Evaluate current market conditions and make trading decision."""
        try:
            price_response = await bitcoin_service.get_current_price()
            if not price_response['success']:
                raise Exception("Failed to fetch current Bitcoin price")
            
            current_price = price_response['data']['current_price']
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
                time_since_last_purchase_hours=None
            )


decision_maker_service = DecisionMakerService()