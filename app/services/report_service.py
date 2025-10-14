"""
Service for generating and sending trading reports.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from jinja2 import Template

from app.models.reporting import (
    WeeklyReportData,
    TradingSummary,
    PortfolioSummary,
    MarketMetrics,
    PerformanceMetrics,
    BotStatus,
    ReportDeliveryStatus,
)
from app.services.decision_maker_service import decision_maker_service
from app.services.bitcoin_service import bitcoin_service
from app.services.persistent_storage_service import persistent_storage_service
from app.services.metrics_calculation_service import metrics_calculation_service
from app.config import settings
from app.core.email_notifier import send_html_email, validate_email_config

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating and delivering trading reports."""

    def __init__(self):
        self.logger = logger

    async def generate_weekly_report_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> WeeklyReportData:
        """
        Generate comprehensive weekly report data.

        Args:
            start_date: Start of report period (defaults to 7 days ago)
            end_date: End of report period (defaults to now)

        Returns:
            WeeklyReportData with all metrics
        """
        # Default to last 7 days if not specified
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        self.logger.info(f"Generating weekly report from {start_date} to {end_date}")

        # Get trading summary
        trading_summary = await self._calculate_trading_summary(start_date, end_date)

        # Get portfolio summary
        portfolio_summary = await self._calculate_portfolio_summary()

        # Get market metrics
        market_metrics = await self._calculate_market_metrics(start_date, end_date)

        # Get performance metrics
        performance_metrics = await self._calculate_performance_metrics(start_date, end_date)

        # Get bot status
        bot_status = await self._get_bot_status()

        # Create period description
        period_description = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

        return WeeklyReportData(
            report_generated_at=datetime.now(),
            period_start=start_date,
            period_end=end_date,
            period_description=period_description,
            trading_summary=trading_summary,
            portfolio_summary=portfolio_summary,
            market_metrics=market_metrics,
            performance_metrics=performance_metrics,
            bot_status=bot_status,
        )

    async def _calculate_trading_summary(
        self, start_date: datetime, end_date: datetime
    ) -> TradingSummary:
        """Calculate trading activity summary for the period."""
        try:
            # Get trading statistics from persistent storage
            stats = persistent_storage_service.get_trading_stats()

            # For this implementation, we'll use all-time stats
            # In production, you'd filter by date range
            total_checks = stats.get("total_checks", 0)
            executed_trades = stats.get("executed_trades", 0)
            skipped_checks = total_checks - executed_trades

            success_rate = (executed_trades / total_checks * 100) if total_checks > 0 else 0.0

            # Get purchase history
            purchase_history = decision_maker_service.get_purchase_history()
            total_invested = purchase_history.total_invested
            avg_price = purchase_history.average_purchase_price if purchase_history.purchases else None

            return TradingSummary(
                total_checks=total_checks,
                executed_trades=executed_trades,
                skipped_checks=skipped_checks,
                success_rate=round(success_rate, 2),
                total_invested=total_invested,
                average_purchase_price=avg_price,
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate trading summary: {e}")
            # Return minimal summary
            return TradingSummary(
                total_checks=0,
                executed_trades=0,
                skipped_checks=0,
                success_rate=0.0,
                total_invested=0.0,
            )

    async def _calculate_portfolio_summary(self) -> PortfolioSummary:
        """Calculate current portfolio status."""
        try:
            purchase_history = decision_maker_service.get_purchase_history()

            # Get current BTC price
            price_response = await bitcoin_service.get_bitcoin_price()
            current_price = price_response.get("data", {}).get("current_price", 0) if price_response.get("success") else 0

            total_btc = purchase_history.total_btc_acquired
            total_invested = purchase_history.total_invested
            current_value = total_btc * current_price

            unrealized_pnl = current_value - total_invested
            unrealized_pnl_pct = (unrealized_pnl / total_invested * 100) if total_invested > 0 else 0

            return PortfolioSummary(
                total_btc=total_btc,
                total_usd_invested=total_invested,
                current_btc_value=current_value,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_percentage=round(unrealized_pnl_pct, 2),
                number_of_purchases=len(purchase_history.purchases),
                average_entry_price=purchase_history.average_purchase_price,
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate portfolio summary: {e}")
            return PortfolioSummary(
                total_btc=0.0,
                total_usd_invested=0.0,
                current_btc_value=0.0,
                unrealized_pnl=0.0,
                unrealized_pnl_percentage=0.0,
                number_of_purchases=0,
                average_entry_price=0.0,
            )

    async def _calculate_market_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> MarketMetrics:
        """Calculate market performance for the period."""
        try:
            # Get current price
            price_response = await bitcoin_service.get_bitcoin_price()
            current_price = price_response.get("data", {}).get("current_price", 0) if price_response.get("success") else 0

            # Get historical candles for the week
            hours_diff = int((end_date - start_date).total_seconds() / 3600)
            candles_response = await bitcoin_service.get_bitcoin_candles(
                hours=min(hours_diff, 168),  # Max 1 week
                granularity="ONE_HOUR"
            )

            if candles_response.get("success") and candles_response.get("data", {}).get("candles"):
                candles = candles_response["data"]["candles"]

                # Calculate metrics from candles
                prices = [c.get("close", 0) for c in candles]
                highs = [c.get("high", 0) for c in candles]
                lows = [c.get("low", 0) for c in candles]
                volumes = [c.get("volume", 0) for c in candles]

                period_start_price = prices[0]
                period_end_price = prices[-1]
                price_change = period_end_price - period_start_price
                price_change_pct = (price_change / period_start_price * 100) if period_start_price > 0 else 0

                # Get metrics snapshot for RSI
                metrics_snapshot = await metrics_calculation_service.get_metrics_snapshot()
                avg_rsi = metrics_snapshot.technical_indicators.rsi_14 if metrics_snapshot.technical_indicators else None

                # Calculate volatility (simplified - std dev of returns)
                returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                volatility = (sum([(r - sum(returns)/len(returns))**2 for r in returns]) / len(returns))**0.5 * 100 if returns else None

                return MarketMetrics(
                    period_start_price=period_start_price,
                    period_end_price=period_end_price,
                    price_change=price_change,
                    price_change_percentage=round(price_change_pct, 2),
                    period_high=max(highs),
                    period_low=min(lows),
                    average_price=sum(prices) / len(prices),
                    volatility=round(volatility, 2) if volatility else None,
                    average_rsi=round(avg_rsi, 1) if avg_rsi else None,
                    average_volume=sum(volumes) / len(volumes) if volumes else None,
                )

            else:
                # Fallback to current price only
                return MarketMetrics(
                    period_start_price=current_price,
                    period_end_price=current_price,
                    price_change=0.0,
                    price_change_percentage=0.0,
                    period_high=current_price,
                    period_low=current_price,
                    average_price=current_price,
                )

        except Exception as e:
            self.logger.error(f"Failed to calculate market metrics: {e}")
            return MarketMetrics(
                period_start_price=0.0,
                period_end_price=0.0,
                price_change=0.0,
                price_change_percentage=0.0,
                period_high=0.0,
                period_low=0.0,
                average_price=0.0,
            )

    async def _calculate_performance_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> PerformanceMetrics:
        """Calculate performance analysis metrics."""
        try:
            purchase_history = decision_maker_service.get_purchase_history()

            if not purchase_history.purchases:
                return PerformanceMetrics()

            # Get current price
            price_response = await bitcoin_service.get_bitcoin_price()
            current_price = price_response.get("data", {}).get("current_price", 0) if price_response.get("success") else 0

            # Find best and worst trades (by price, not necessarily by return)
            purchases = purchase_history.purchases
            best_purchase = min(purchases, key=lambda p: p.price)
            worst_purchase = max(purchases, key=lambda p: p.price)

            best_return = ((current_price - best_purchase.price) / best_purchase.price * 100) if best_purchase.price > 0 else 0
            worst_return = ((current_price - worst_purchase.price) / worst_purchase.price * 100) if worst_purchase.price > 0 else 0

            # Calculate total return
            total_invested = purchase_history.total_invested
            current_value = purchase_history.total_btc_acquired * current_price
            total_return = ((current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0

            return PerformanceMetrics(
                best_trade={
                    "date": best_purchase.timestamp.strftime("%b %d"),
                    "price": f"${best_purchase.price:,.2f}",
                    "return_pct": f"{best_return:+.2f}%"
                },
                worst_trade={
                    "date": worst_purchase.timestamp.strftime("%b %d"),
                    "price": f"${worst_purchase.price:,.2f}",
                    "return_pct": f"{worst_return:+.2f}%"
                },
                total_return=round(total_return, 2),
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate performance metrics: {e}")
            return PerformanceMetrics()

    async def _get_bot_status(self) -> BotStatus:
        """Get current bot operational status."""
        try:
            # Get bot state from persistent storage
            bot_state = persistent_storage_service.load_bot_state()

            is_running = bot_state.get("is_running", False)
            start_time_str = bot_state.get("start_time")

            uptime_days = 0.0
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str)
                    uptime_days = (datetime.now() - start_time).total_seconds() / 86400
                except Exception:
                    pass

            return BotStatus(
                is_running=is_running,
                uptime_days=round(uptime_days, 1),
                total_errors=bot_state.get("total_errors", 0),
                last_error=bot_state.get("last_error"),
            )

        except Exception as e:
            self.logger.error(f"Failed to get bot status: {e}")
            return BotStatus(
                is_running=False,
                uptime_days=0.0,
                total_errors=0,
            )

    async def generate_report_html(self, report_data: WeeklyReportData) -> str:
        """
        Generate HTML email from report data.

        Args:
            report_data: Weekly report data

        Returns:
            HTML string
        """
        # Load template
        template_path = Path(__file__).parent.parent / "templates" / "email" / "weekly_report.html"

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
        except FileNotFoundError:
            self.logger.error(f"Template not found at {template_path}, using fallback")
            template_content = self._get_fallback_template()

        # Render template with data
        template = Template(template_content)
        html = template.render(report=report_data)

        return html

    def _get_fallback_template(self) -> str:
        """Get a simple fallback template if main template is missing."""
        return """
        <html>
        <head><style>body{font-family:Arial,sans-serif;max-width:600px;margin:0 auto;}</style></head>
        <body>
            <h1>📊 Weekly Trading Report</h1>
            <p>{{ report.period_description }}</p>
            <h2>Portfolio: ${{ "%.2f"|format(report.portfolio_summary.current_btc_value) }}</h2>
            <p>P&L: {{ "%.2f"|format(report.portfolio_summary.unrealized_pnl_percentage) }}%</p>
        </body>
        </html>
        """

    async def send_weekly_email_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        recipient_override: Optional[str] = None
    ) -> ReportDeliveryStatus:
        """
        Generate and send weekly email report.

        Args:
            start_date: Start of report period
            end_date: End of report period
            recipient_override: Override default email recipient

        Returns:
            ReportDeliveryStatus with delivery info
        """
        try:
            # Check if email is configured
            if not validate_email_config(
                smtp_host=settings.email_smtp_host,
                email_from=settings.email_from,
                email_password=settings.email_password,
                email_to=settings.email_to,
            ):
                self.logger.warning("Email not configured, cannot send weekly report")
                return ReportDeliveryStatus(
                    success=False,
                    report_type="weekly",
                    recipient=settings.email_to or "not_configured",
                    delivery_method="email",
                    error_message="Email configuration incomplete"
                )

            # Generate report data
            report_data = await self.generate_weekly_report_data(start_date, end_date)

            # Generate HTML
            html_body = await self.generate_report_html(report_data)

            # Generate plain text version
            plain_text = self._generate_plain_text(report_data)

            # Determine recipient
            recipient = recipient_override or settings.email_to

            # Send email
            send_html_email(
                subject=f"📊 BTC Trading Bot - Weekly Report ({report_data.period_description})",
                html_body=html_body,
                plain_text_body=plain_text,
                smtp_host=settings.email_smtp_host,
                smtp_port=settings.email_smtp_port,
                email_from=settings.email_from,
                email_password=settings.email_password,
                email_to=recipient,
            )

            self.logger.info(f"Weekly report sent successfully to {recipient}")

            return ReportDeliveryStatus(
                success=True,
                report_type="weekly",
                delivered_at=datetime.now(),
                recipient=recipient,
                delivery_method="email",
            )

        except Exception as e:
            self.logger.error(f"Failed to send weekly report: {e}")
            return ReportDeliveryStatus(
                success=False,
                report_type="weekly",
                recipient=recipient_override or settings.email_to or "unknown",
                delivery_method="email",
                error_message=str(e),
            )

    def _generate_plain_text(self, report_data: WeeklyReportData) -> str:
        """Generate plain text version of report for email fallback."""
        portfolio = report_data.portfolio_summary
        trading = report_data.trading_summary
        market = report_data.market_metrics

        pnl_sign = "+" if portfolio.unrealized_pnl >= 0 else ""

        text = f"""
📊 BTC Trading Bot - Weekly Report
{report_data.period_description}

Portfolio Performance
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Total Invested: ${portfolio.total_usd_invested:,.2f}
🪙 Total BTC: {portfolio.total_btc:.8f} BTC
📈 Current Value: ${portfolio.current_btc_value:,.2f}
💵 Unrealized P&L: {pnl_sign}${portfolio.unrealized_pnl:,.2f} ({pnl_sign}{portfolio.unrealized_pnl_percentage:.2f}%)

Trading Activity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Executed Trades: {trading.executed_trades}
📊 Total Checks: {trading.total_checks}
🎯 Success Rate: {trading.success_rate:.2f}%
💵 Average Purchase: ${trading.average_purchase_price:,.2f if trading.average_purchase_price else 0}

Market Performance
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Week Start: ${market.period_start_price:,.2f}
📊 Week End: ${market.period_end_price:,.2f}
📈 Change: ${market.price_change:+,.2f} ({market.price_change_percentage:+.2f}%)

Bot Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 Status: {"Running" if report_data.bot_status.is_running else "Stopped"}
⏱ Uptime: {report_data.bot_status.uptime_days:.1f} days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BTC Trading Bot 2.0 | Powered by FastAPI
        """.strip()

        return text


# Global service instance
report_service = ReportService()
