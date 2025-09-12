"""
Enhanced notification service for different message types and rich formatting.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from app.models.trading import TradingDecision, SimulatedTrade, PurchaseHistory
from app.services.telegram_service import telegram_service
from app.services.persistent_storage_service import persistent_storage_service

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Enumeration of notification types."""

    TRADE_EXECUTED = "trade_executed"
    TRADE_SKIPPED = "trade_skipped"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    DAILY_SUMMARY = "daily_summary"
    ERROR = "error"
    CONFIG_UPDATED = "config_updated"
    MANUAL_CHECK = "manual_check"


class NotificationService:
    """Enhanced service for managing different types of notifications."""

    def __init__(self):
        self.logger = logger
        self.notification_history = []

    async def send_trade_executed(
        self,
        decision: TradingDecision,
        simulated_trade: SimulatedTrade,
        purchase_history: Optional[PurchaseHistory] = None,
    ):
        """Send notification for executed trade."""
        btc_amount = decision.recommended_amount_usd / decision.current_price

        message = self._format_trade_executed_message(
            amount_usd=decision.recommended_amount_usd,
            btc_amount=btc_amount,
            price=decision.current_price,
            reason=decision.reason,
            last_price=decision.last_purchase_price,
            price_drop=decision.price_drop_percentage,
            daily_count=simulated_trade.daily_trade_count,
            timestamp=simulated_trade.timestamp,
        )

        if purchase_history:
            message += f"\n\n📊 Portfolio Update:\n"
            message += f"💰 Total Invested: ${purchase_history.total_invested:,.2f}\n"
            message += f"🪙 Total BTC: {purchase_history.total_btc_acquired:.8f}\n"
            message += f"💵 Avg Price: ${purchase_history.average_purchase_price:,.2f}"

        await self._send_notification(message, NotificationType.TRADE_EXECUTED)

    async def send_trade_skipped(
        self, decision: TradingDecision, reason: str, check_number: int
    ):
        """Send notification for skipped trade."""
        message = self._format_trade_skipped_message(
            reason=reason,
            current_price=decision.current_price,
            last_price=decision.last_purchase_price,
            price_drop=decision.price_drop_percentage,
            check_number=check_number,
        )

        await self._send_notification(message, NotificationType.TRADE_SKIPPED)

    async def send_bot_started(self, interval_minutes: int, next_check: datetime):
        """Send notification when bot starts."""
        message = (
            f"🤖 Trading Bot Started\n\n"
            f"⏰ Check Interval: {interval_minutes} minutes\n"
            f"🕐 Next Check: {next_check.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🟢 Status: Active and monitoring"
        )

        await self._send_notification(message, NotificationType.BOT_STARTED)

    async def send_bot_stopped(self):
        """Send notification when bot stops."""
        message = (
            f"🛑 Trading Bot Stopped\n\n"
            f"🔴 Status: Inactive\n"
            f"🕐 Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        await self._send_notification(message, NotificationType.BOT_STOPPED)

    async def send_daily_summary(
        self,
        checks_today: int,
        trades_today: int,
        purchase_history: PurchaseHistory,
        total_checks: int,
        total_trades: int,
    ):
        """Send daily summary notification."""
        execution_rate = (trades_today / checks_today * 100) if checks_today > 0 else 0

        message = (
            f"🌅 Daily Trading Summary\n\n"
            f"📊 Today's Activity:\n"
            f"🔍 Checks: {checks_today}\n"
            f"✅ Trades: {trades_today}\n"
            f"📈 Success Rate: {execution_rate:.1f}%\n\n"
            f"💼 Portfolio Status:\n"
            f"💰 Total Invested: ${purchase_history.total_invested:,.2f}\n"
            f"🪙 Total BTC: {purchase_history.total_btc_acquired:.8f}\n"
            f"💵 Average Price: ${purchase_history.average_purchase_price:,.2f}\n\n"
            f"📈 All-Time Stats:\n"
            f"🔍 Total Checks: {total_checks}\n"
            f"✅ Total Trades: {total_trades}\n"
            f"📊 Overall Rate: {(total_trades/total_checks*100) if total_checks > 0 else 0:.1f}%"
        )

        await self._send_notification(message, NotificationType.DAILY_SUMMARY)

    async def send_error_notification(self, error_message: str, context: str = ""):
        """Send error notification."""
        message = (
            f"❌ Trading Bot Error\n\n"
            f"🔴 Error: {error_message}\n"
            f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if context:
            message += f"\n📝 Context: {context}"

        await self._send_notification(message, NotificationType.ERROR)

    async def send_config_updated(self, old_config: Dict, new_config: Dict):
        """Send notification when configuration is updated."""
        changes = []

        for key in new_config:
            if key in old_config and old_config[key] != new_config[key]:
                changes.append(f"• {key}: {old_config[key]} → {new_config[key]}")

        message = (
            f"⚙️ Configuration Updated\n\n"
            f"📝 Changes:\n"
            + "\n".join(changes)
            + f"\n\n🕐 Updated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        await self._send_notification(message, NotificationType.CONFIG_UPDATED)

    async def send_manual_check_result(self, success: bool, details: str = ""):
        """Send notification for manual check results."""
        if success:
            message = (
                f"🔍 Manual Check Completed\n\n"
                f"✅ Status: Success\n"
                f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}"
            )
        else:
            message = (
                f"🔍 Manual Check Failed\n\n"
                f"❌ Status: Error\n"
                f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}"
            )

        if details:
            message += f"\n📝 Details: {details}"

        await self._send_notification(message, NotificationType.MANUAL_CHECK)

    def _format_trade_executed_message(
        self,
        amount_usd: float,
        btc_amount: float,
        price: float,
        reason: str,
        last_price: Optional[float],
        price_drop: Optional[float],
        daily_count: int,
        timestamp: datetime,
    ) -> str:
        """Format a trade executed message."""
        message = (
            f"✅ SIMULATED TRADE EXECUTED\n\n"
            f"💰 Investment: ${amount_usd:,.2f}\n"
            f"🪙 BTC Acquired: {btc_amount:.8f}\n"
            f"💵 Current Price: ${price:,.2f}\n"
            f"📈 Trigger: {reason}\n"
        )

        if last_price and price_drop:
            message += (
                f"📊 Previous Price: ${last_price:,.2f}\n"
                f"📉 Drop: {price_drop:.2f}%\n"
            )

        message += (
            f"🔢 Trade #{daily_count} today\n"
            f"🕐 {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        return message

    def _format_trade_skipped_message(
        self,
        reason: str,
        current_price: float,
        last_price: Optional[float],
        price_drop: Optional[float],
        check_number: int,
    ) -> str:
        """Format a trade skipped message."""
        message = (
            f"⏭️ Trade Skipped\n\n"
            f"📝 Reason: {reason}\n"
            f"💰 Current Price: ${current_price:,.2f}\n"
        )

        if last_price:
            message += f"📊 Last Purchase: ${last_price:,.2f}\n"

        if price_drop is not None:
            message += f"📉 Price Change: {price_drop:.2f}%\n"

        message += f"🔍 Check #{check_number} today\n"
        message += f"🕐 {datetime.now().strftime('%H:%M:%S')}"

        return message

    async def _send_notification(
        self, message: str, notification_type: NotificationType
    ):
        """Send notification and log to history."""
        try:
            await telegram_service.send_message(message)

            # Add to in-memory history
            self.notification_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": notification_type.value,
                    "message": message,
                    "success": True,
                }
            )

            # Save to persistent storage
            persistent_storage_service.save_notification(
                notification_type.value, message, success=True
            )

            self.logger.info(f"Sent {notification_type.value} notification")

        except Exception as e:
            self.logger.error(
                f"Failed to send {notification_type.value} notification: {e}"
            )

            # Add failed notification to in-memory history
            self.notification_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": notification_type.value,
                    "message": message,
                    "success": False,
                    "error": str(e),
                }
            )

            # Save to persistent storage
            persistent_storage_service.save_notification(
                notification_type.value, message, success=False, error=str(e)
            )

    def get_notification_history(self, limit: int = 50) -> list:
        """Get recent notification history."""
        return self.notification_history[-limit:] if self.notification_history else []


# Global service instance
notification_service = NotificationService()
