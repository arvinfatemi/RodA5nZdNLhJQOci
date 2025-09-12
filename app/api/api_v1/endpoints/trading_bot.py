"""
API endpoints for trading bot control and monitoring.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.trading import TradingBotStatus
from app.services.scheduler_service import scheduler_service
from app.services.simulated_trading_service import simulated_trading_service
from app.services.decision_maker_service import decision_maker_service

logger = logging.getLogger(__name__)

router = APIRouter()


class BotControlRequest(BaseModel):
    """Request model for bot control operations."""

    interval_minutes: Optional[int] = None  # If None, uses config value


class ManualCheckResponse(BaseModel):
    """Response model for manual trading checks."""

    success: bool
    message: str
    timestamp: datetime


@router.get("/status", response_model=TradingBotStatus)
async def get_bot_status():
    """Get current trading bot status."""
    try:
        status = scheduler_service.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_bot(request: BotControlRequest):
    """Start the trading bot with specified or configured interval."""
    try:
        await scheduler_service.start_scheduler(
            interval_minutes=request.interval_minutes
        )
        
        # Get the actual interval used (either from request or config)
        actual_interval = request.interval_minutes
        if actual_interval is None:
            try:
                dca_config = await decision_maker_service.get_dca_config()
                actual_interval = dca_config.data_fetch_interval
            except:
                actual_interval = 30  # fallback
        
        return {
            "success": True,
            "message": f"Trading bot started with {actual_interval}-minute intervals",
            "status": scheduler_service.get_status(),
        }
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_bot():
    """Stop the trading bot."""
    try:
        await scheduler_service.stop_scheduler()
        return {
            "success": True,
            "message": "Trading bot stopped",
            "status": scheduler_service.get_status(),
        }
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check", response_model=ManualCheckResponse)
async def trigger_manual_check():
    """Trigger an immediate trading check."""
    try:
        success = await scheduler_service.trigger_immediate_check()

        if success:
            return ManualCheckResponse(
                success=True,
                message="Manual trading check completed successfully",
                timestamp=datetime.now(),
            )
        else:
            return ManualCheckResponse(
                success=False,
                message="Manual trading check failed - check logs for details",
                timestamp=datetime.now(),
            )

    except Exception as e:
        logger.error(f"Error triggering manual check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_trading_history():
    """Get comprehensive trading history and statistics."""
    try:
        # Get simulated trading summary
        trading_summary = simulated_trading_service.get_trading_summary()

        # Get purchase history from decision maker
        purchase_history = decision_maker_service.get_purchase_history()

        # Get current config
        dca_config = await decision_maker_service.get_dca_config()

        # Get bot status
        bot_status = scheduler_service.get_status()

        return {
            "success": True,
            "data": {
                "trading_summary": trading_summary,
                "purchase_history": {
                    "total_invested": purchase_history.total_invested,
                    "total_btc_acquired": purchase_history.total_btc_acquired,
                    "average_purchase_price": purchase_history.average_purchase_price,
                    "last_purchase_price": purchase_history.last_purchase_price,
                    "last_purchase_timestamp": purchase_history.last_purchase_timestamp,
                    "total_purchases": len(purchase_history.purchases),
                    "recent_purchases": [
                        {
                            "timestamp": p.timestamp,
                            "price": p.price,
                            "amount_usd": p.amount_usd,
                            "amount_btc": p.amount_btc,
                            "strategy": p.strategy,
                        }
                        for p in purchase_history.purchases[-10:]  # Last 10 purchases
                    ],
                },
                "current_config": {
                    "purchase_amount_usd": dca_config.purchase_amount_usd,
                    "drop_percentage_threshold": dca_config.drop_percentage_threshold,
                    "trading_enabled": dca_config.trading_enabled,
                    "max_daily_trades": dca_config.max_daily_trades,
                    "data_fetch_interval": dca_config.data_fetch_interval,
                },
                "bot_status": {
                    "is_running": bot_status.is_running,
                    "last_check_time": bot_status.last_check_time,
                    "next_check_time": bot_status.next_check_time,
                    "total_checks_today": bot_status.total_checks_today,
                    "total_trades_today": bot_status.total_trades_today,
                    "uptime_seconds": bot_status.uptime_seconds,
                },
            },
        }

    except Exception as e:
        logger.error(f"Error getting trading history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_bot_summary():
    """Get a concise summary of bot performance."""
    try:
        # Get key metrics
        trading_summary = simulated_trading_service.get_trading_summary()
        purchase_history = decision_maker_service.get_purchase_history()
        bot_status = scheduler_service.get_status()

        # Calculate performance metrics
        total_checks = trading_summary.get("statistics", {}).get("total_checks", 0)
        executed_trades = trading_summary.get("statistics", {}).get(
            "executed_trades", 0
        )
        execution_rate = trading_summary.get("statistics", {}).get(
            "execution_rate_percent", 0
        )

        return {
            "success": True,
            "summary": {
                "bot_running": bot_status.is_running,
                "uptime_hours": round((bot_status.uptime_seconds or 0) / 3600, 2),
                "checks_today": bot_status.total_checks_today,
                "trades_today": bot_status.total_trades_today,
                "total_checks": total_checks,
                "total_trades": executed_trades,
                "execution_rate": f"{execution_rate}%",
                "total_invested": purchase_history.total_invested,
                "total_btc": purchase_history.total_btc_acquired,
                "avg_price": purchase_history.average_purchase_price,
                "last_check": bot_status.last_check_time,
                "next_check": bot_status.next_check_time,
            },
        }

    except Exception as e:
        logger.error(f"Error getting bot summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/csv")
async def export_trading_data():
    """Export trading data to CSV format."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trading_history_{timestamp}.csv"

        success = simulated_trading_service.export_trades_to_csv(filename)

        if success:
            return {
                "success": True,
                "message": f"Trading data exported successfully to {filename}",
                "filename": filename,
            }
        else:
            return {"success": False, "message": "Failed to export trading data"}

    except Exception as e:
        logger.error(f"Error exporting trading data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
