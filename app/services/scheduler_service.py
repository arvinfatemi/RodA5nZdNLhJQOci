"""
Background scheduler service for automated trading bot.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.models.trading import TradingBotStatus
from app.services.decision_maker_service import decision_maker_service
from app.services.telegram_service import telegram_service
from app.services.simulated_trading_service import simulated_trading_service
from app.services.notification_service import notification_service
from app.services.persistent_storage_service import persistent_storage_service

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing background trading automation."""

    def __init__(self):
        self.logger = logger
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.status = TradingBotStatus(is_running=False)
        self.start_time: Optional[datetime] = None
        self._daily_reset_time: Optional[datetime] = None

    async def start_scheduler(self, interval_minutes: Optional[int] = None):
        """Start the background scheduler."""
        if self.scheduler and self.scheduler.running:
            self.logger.warning("Scheduler is already running")
            return

        # Get interval from config if not provided
        if interval_minutes is None:
            try:
                dca_config = await decision_maker_service.get_dca_config()
                interval_minutes = dca_config.data_fetch_interval
                self.logger.info(f"Using data_fetch_interval from config: {interval_minutes} minutes")
            except Exception as e:
                self.logger.warning(f"Failed to get config interval, using default 30 minutes: {e}")
                interval_minutes = 30

        self.scheduler = AsyncIOScheduler()

        # Add the trading check job
        self.scheduler.add_job(
            self._run_trading_check,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="trading_check",
            replace_existing=True,
            max_instances=1,
        )

        # Add daily reset job at midnight
        self.scheduler.add_job(
            self._daily_reset,
            trigger=IntervalTrigger(hours=24),
            id="daily_reset",
            replace_existing=True,
            next_run_time=self._get_next_midnight(),
        )

        try:
            self.scheduler.start()
            self.start_time = datetime.now()
            self.status.is_running = True
            self.status.last_error = None

            # Save bot state to persistent storage
            persistent_storage_service.save_bot_state(
                is_running=True, start_time=self.start_time
            )

            next_run = self.scheduler.get_job("trading_check").next_run_time
            self.status.next_check_time = next_run

            self.logger.info(
                f"Background scheduler started with {interval_minutes}-minute intervals"
            )
            self.logger.info(f"Next trading check scheduled for: {next_run}")

            # Send startup notification
            await notification_service.send_bot_started(interval_minutes, next_run)

        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            self.status.last_error = str(e)
            raise

    async def stop_scheduler(self):
        """Stop the background scheduler."""
        if not self.scheduler:
            self.logger.warning("No scheduler to stop")
            return

        try:
            self.scheduler.shutdown(wait=True)
            self.status.is_running = False
            self.status.next_check_time = None

            # Save final bot state to persistent storage
            persistent_storage_service.save_bot_state(
                is_running=False,
                total_checks_today=self.status.total_checks_today,
                total_trades_today=self.status.total_trades_today,
                last_error=self.status.last_error,
            )

            self.logger.info("Background scheduler stopped")

            # Send shutdown notification
            await notification_service.send_bot_stopped()

        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")
            self.status.last_error = str(e)
            raise

    def get_status(self) -> TradingBotStatus:
        """Get current scheduler status."""
        if self.scheduler and self.scheduler.running:
            # Update uptime
            if self.start_time:
                self.status.uptime_seconds = (
                    datetime.now() - self.start_time
                ).total_seconds()

            # Update next check time
            job = self.scheduler.get_job("trading_check")
            if job:
                self.status.next_check_time = job.next_run_time

        return self.status

    async def trigger_immediate_check(self) -> bool:
        """Trigger an immediate trading check."""
        if not self.status.is_running:
            self.logger.warning("Cannot trigger check - scheduler is not running")
            return False

        try:
            self.logger.info("Triggering immediate trading check")
            await self._run_trading_check()
            return True
        except Exception as e:
            self.logger.error(f"Failed to trigger immediate check: {e}")
            self.status.last_error = str(e)
            return False

    async def _run_trading_check(self):
        """Execute a trading check cycle."""
        check_time = datetime.now()
        self.status.last_check_time = check_time
        self.status.total_checks_today += 1

        self.logger.info(f"Starting trading check #{self.status.total_checks_today}")

        try:
            # Get current DCA configuration
            dca_config = await decision_maker_service.get_dca_config()

            if not dca_config.trading_enabled:
                self.logger.info("Trading is disabled in configuration, skipping check")
                # Use a dummy decision for the notification
                from app.models.trading import TradingDecision

                dummy_decision = TradingDecision(
                    should_buy=False,
                    reason="Trading disabled in configuration",
                    current_price=0.0,
                    last_purchase_price=None,
                    price_drop_percentage=None,
                    recommended_amount_usd=None,
                )
                await notification_service.send_trade_skipped(
                    dummy_decision,
                    "Trading disabled in configuration",
                    self.status.total_checks_today,
                )
                return

            # Check daily trade limit
            if self.status.total_trades_today >= dca_config.max_daily_trades:
                self.logger.info(
                    f"Daily trade limit reached ({dca_config.max_daily_trades}), skipping check"
                )
                # Use a dummy decision for the notification
                dummy_decision = TradingDecision(
                    should_buy=False,
                    reason=f"Daily trade limit reached ({dca_config.max_daily_trades})",
                    current_price=0.0,
                    last_purchase_price=None,
                    price_drop_percentage=None,
                    recommended_amount_usd=None,
                )
                await notification_service.send_trade_skipped(
                    dummy_decision,
                    f"Daily trade limit reached ({dca_config.max_daily_trades})",
                    self.status.total_checks_today,
                )
                return

            # Evaluate current market conditions with metrics
            market_evaluation = await decision_maker_service.evaluate_market_with_metrics()
            decision = market_evaluation["enhanced_decision"]
            metrics_snapshot = market_evaluation.get("metrics_snapshot")

            # Execute simulated trade (handles all logic internally)
            simulated_trade = await simulated_trading_service.execute_simulated_trade(
                decision, dca_config
            )

            if simulated_trade.executed:
                self.status.total_trades_today += 1
                # Send trade executed notification with portfolio info and metrics
                purchase_history = decision_maker_service.get_purchase_history()
                await notification_service.send_trade_executed(
                    decision, simulated_trade, purchase_history, metrics_snapshot
                )
            else:
                # Send skip notification with metrics
                await notification_service.send_trade_skipped(
                    decision, simulated_trade.reason, self.status.total_checks_today, metrics_snapshot
                )

            self.status.last_error = None

        except Exception as e:
            self.logger.error(f"Trading check failed: {e}")
            self.status.last_error = str(e)

            await notification_service.send_error_notification(
                str(e), f"Trading check #{self.status.total_checks_today}"
            )

    def _get_next_midnight(self) -> datetime:
        """Get the next midnight for daily reset scheduling."""
        now = datetime.now()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=1
        )
        return tomorrow

    async def _daily_reset(self):
        """Reset daily counters at midnight."""
        self.status.total_checks_today = 0
        self.status.total_trades_today = 0
        self._daily_reset_time = datetime.now()

        # Record daily reset in persistent storage
        persistent_storage_service.record_daily_reset()

        self.logger.info("Daily counters reset")

        # Get summary stats
        history = decision_maker_service.get_purchase_history()

        # Get trading summary for the daily notification
        trading_summary = simulated_trading_service.get_trading_summary()
        stats = trading_summary.get("statistics", {})

        await notification_service.send_daily_summary(
            checks_today=self.status.total_checks_today,
            trades_today=self.status.total_trades_today,
            purchase_history=history,
            total_checks=stats.get("total_checks", 0),
            total_trades=stats.get("executed_trades", 0),
        )


# Global service instance
scheduler_service = SchedulerService()
