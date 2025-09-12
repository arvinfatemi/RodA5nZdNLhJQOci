"""
Simulated trading service with detailed logging for reporting.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.models.trading import (
    PurchaseRecord,
    TradingDecision,
    DCAConfig,
    SimulatedTrade,
)
from app.services.decision_maker_service import decision_maker_service

logger = logging.getLogger(__name__)


class SimulatedTradingService:
    """Service for executing and logging simulated trades."""

    def __init__(self, log_file_path: str = "simulated_trades.json"):
        self.logger = logger
        self.log_file_path = Path(log_file_path)
        self.daily_trade_count = 0
        self._last_reset_date: Optional[str] = None
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        """Ensure the log file exists and is properly initialized."""
        if not self.log_file_path.exists():
            initial_data = {
                "trades": [],
                "summary": {
                    "total_trades": 0,
                    "total_invested": 0.0,
                    "total_btc_acquired": 0.0,
                    "first_trade": None,
                    "last_trade": None,
                    "created_at": datetime.now().isoformat(),
                },
            }
            self._write_to_log_file(initial_data)
            self.logger.info(
                f"Created new simulated trading log file: {self.log_file_path}"
            )

    def _read_log_file(self) -> Dict[str, Any]:
        """Read and parse the trading log file."""
        try:
            with open(self.log_file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error reading log file: {e}")
            return {"trades": [], "summary": {}}

    def _write_to_log_file(self, data: Dict[str, Any]):
        """Write data to the trading log file."""
        try:
            with open(self.log_file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error writing to log file: {e}")
            raise

    def _check_daily_reset(self):
        """Check if we need to reset daily counters."""
        today = datetime.now().strftime("%Y-%m-%d")
        if self._last_reset_date != today:
            self.daily_trade_count = 0
            self._last_reset_date = today
            self.logger.info(f"Daily trade counter reset for {today}")

    async def execute_simulated_trade(
        self, decision: TradingDecision, dca_config: DCAConfig
    ) -> SimulatedTrade:
        """Execute a simulated trade and log it comprehensively."""
        self._check_daily_reset()

        trade_time = datetime.now()

        # Check if trading is enabled
        if not dca_config.trading_enabled:
            simulated_trade = SimulatedTrade(
                timestamp=trade_time,
                decision=decision,
                executed=False,
                reason="Trading disabled in configuration",
                daily_trade_count=self.daily_trade_count,
            )
            self._log_trade(simulated_trade, None)
            return simulated_trade

        # Check daily trade limit
        if self.daily_trade_count >= dca_config.max_daily_trades:
            simulated_trade = SimulatedTrade(
                timestamp=trade_time,
                decision=decision,
                executed=False,
                reason=f"Daily trade limit reached ({dca_config.max_daily_trades})",
                daily_trade_count=self.daily_trade_count,
            )
            self._log_trade(simulated_trade, None)
            return simulated_trade

        # Check if decision recommends buying
        if not decision.should_buy:
            simulated_trade = SimulatedTrade(
                timestamp=trade_time,
                decision=decision,
                executed=False,
                reason=f"Decision not to buy: {decision.reason}",
                daily_trade_count=self.daily_trade_count,
            )
            self._log_trade(simulated_trade, None)
            return simulated_trade

        # Execute the simulated trade
        btc_amount = decision.recommended_amount_usd / decision.current_price

        purchase_record = PurchaseRecord(
            timestamp=trade_time,
            price=decision.current_price,
            amount_usd=decision.recommended_amount_usd,
            amount_btc=btc_amount,
            strategy="dca_simulated",
        )

        # Add to decision maker's history
        decision_maker_service.add_purchase_record(purchase_record)

        # Update counters
        self.daily_trade_count += 1

        simulated_trade = SimulatedTrade(
            timestamp=trade_time,
            decision=decision,
            executed=True,
            reason=f"Trade executed: {decision.reason}",
            daily_trade_count=self.daily_trade_count,
        )

        # Log the successful trade
        self._log_trade(simulated_trade, purchase_record)

        self.logger.info(
            f"Simulated trade executed: ${decision.recommended_amount_usd:,.2f} -> {btc_amount:.8f} BTC at ${decision.current_price:,.2f}"
        )

        return simulated_trade

    def _log_trade(
        self, simulated_trade: SimulatedTrade, purchase_record: Optional[PurchaseRecord]
    ):
        """Log a trade to the persistent log file."""
        try:
            log_data = self._read_log_file()

            # Create comprehensive trade log entry
            trade_log_entry = {
                "timestamp": simulated_trade.timestamp.isoformat(),
                "executed": simulated_trade.executed,
                "reason": simulated_trade.reason,
                "daily_trade_count": simulated_trade.daily_trade_count,
                "decision": {
                    "should_buy": simulated_trade.decision.should_buy,
                    "reason": simulated_trade.decision.reason,
                    "current_price": simulated_trade.decision.current_price,
                    "last_purchase_price": simulated_trade.decision.last_purchase_price,
                    "price_drop_percentage": simulated_trade.decision.price_drop_percentage,
                    "recommended_amount_usd": simulated_trade.decision.recommended_amount_usd,
                },
            }

            # Add purchase details if trade was executed
            if purchase_record:
                trade_log_entry["purchase"] = {
                    "amount_usd": purchase_record.amount_usd,
                    "amount_btc": purchase_record.amount_btc,
                    "price": purchase_record.price,
                    "exchange": purchase_record.exchange,
                    "strategy": purchase_record.strategy,
                }

                # Update summary statistics
                summary = log_data.get("summary", {})
                summary["total_trades"] = summary.get("total_trades", 0) + 1
                summary["total_invested"] = (
                    summary.get("total_invested", 0.0) + purchase_record.amount_usd
                )
                summary["total_btc_acquired"] = (
                    summary.get("total_btc_acquired", 0.0) + purchase_record.amount_btc
                )
                summary["last_trade"] = simulated_trade.timestamp.isoformat()

                if not summary.get("first_trade"):
                    summary["first_trade"] = simulated_trade.timestamp.isoformat()

                log_data["summary"] = summary

            # Add the trade to the log
            log_data["trades"].append(trade_log_entry)

            # Write back to file
            self._write_to_log_file(log_data)

        except Exception as e:
            self.logger.error(f"Failed to log trade to file: {e}")

    def get_trading_summary(self) -> Dict[str, Any]:
        """Get a summary of all simulated trading activity."""
        try:
            log_data = self._read_log_file()

            trades = log_data.get("trades", [])
            summary = log_data.get("summary", {})

            # Calculate additional statistics
            executed_trades = [t for t in trades if t.get("executed", False)]
            total_checks = len(trades)
            execution_rate = (
                (len(executed_trades) / total_checks) * 100 if total_checks > 0 else 0
            )

            # Get recent activity (last 10 trades)
            recent_trades = trades[-10:] if trades else []

            return {
                "summary": summary,
                "statistics": {
                    "total_checks": total_checks,
                    "executed_trades": len(executed_trades),
                    "execution_rate_percent": round(execution_rate, 2),
                    "daily_trade_count": self.daily_trade_count,
                },
                "recent_activity": recent_trades,
            }

        except Exception as e:
            self.logger.error(f"Error generating trading summary: {e}")
            return {"error": str(e)}

    def get_trades_for_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get trades within a specific date range."""
        try:
            log_data = self._read_log_file()
            trades = log_data.get("trades", [])

            filtered_trades = []
            for trade in trades:
                trade_time = datetime.fromisoformat(trade["timestamp"])
                if start_date <= trade_time <= end_date:
                    filtered_trades.append(trade)

            return filtered_trades

        except Exception as e:
            self.logger.error(f"Error filtering trades by date: {e}")
            return []

    def export_trades_to_csv(self, output_path: str) -> bool:
        """Export trading history to CSV format."""
        try:
            import csv

            log_data = self._read_log_file()
            trades = log_data.get("trades", [])

            with open(output_path, "w", newline="") as csvfile:
                fieldnames = [
                    "timestamp",
                    "executed",
                    "reason",
                    "daily_trade_count",
                    "should_buy",
                    "current_price",
                    "last_purchase_price",
                    "price_drop_percentage",
                    "recommended_amount_usd",
                    "amount_usd",
                    "amount_btc",
                    "strategy",
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for trade in trades:
                    row = {
                        "timestamp": trade["timestamp"],
                        "executed": trade["executed"],
                        "reason": trade["reason"],
                        "daily_trade_count": trade["daily_trade_count"],
                        "should_buy": trade["decision"]["should_buy"],
                        "current_price": trade["decision"]["current_price"],
                        "last_purchase_price": trade["decision"]["last_purchase_price"],
                        "price_drop_percentage": trade["decision"][
                            "price_drop_percentage"
                        ],
                        "recommended_amount_usd": trade["decision"][
                            "recommended_amount_usd"
                        ],
                        "amount_usd": trade.get("purchase", {}).get("amount_usd", ""),
                        "amount_btc": trade.get("purchase", {}).get("amount_btc", ""),
                        "strategy": trade.get("purchase", {}).get("strategy", ""),
                    }
                    writer.writerow(row)

            self.logger.info(f"Exported {len(trades)} trades to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting trades to CSV: {e}")
            return False


# Global service instance
simulated_trading_service = SimulatedTradingService()
