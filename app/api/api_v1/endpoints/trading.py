"""
Trading decision endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException

from app.models.trading import TradingDecisionResponse, PurchaseRecord, DCAConfig
from app.services.decision_maker_service import decision_maker_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trading")


@router.get("/decision", response_model=TradingDecisionResponse)
async def get_trading_decision():
    """Get current trading decision based on market conditions and DCA strategy."""
    try:
        decision = await decision_maker_service.evaluate_current_market()
        purchase_history = decision_maker_service.get_purchase_history()
        
        dca_config = decision_maker_service.get_dca_config()
        
        history_summary = {
            "total_purchases": len(purchase_history.purchases),
            "total_invested_usd": purchase_history.total_invested,
            "total_btc_acquired": purchase_history.total_btc_acquired,
            "average_price": purchase_history.average_purchase_price,
            "last_purchase_price": purchase_history.last_purchase_price,
            "last_purchase_date": purchase_history.last_purchase_timestamp.isoformat() if purchase_history.last_purchase_timestamp else None
        }
        
        return TradingDecisionResponse(
            success=True,
            decision=decision,
            config=dca_config,
            purchase_history_summary=history_summary
        )
        
    except Exception as e:
        logger.error(f"Failed to get trading decision: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trading decision: {str(e)}")


@router.get("/history")
async def get_purchase_history():
    """Get Bitcoin purchase history."""
    try:
        history = decision_maker_service.get_purchase_history()
        return {
            "success": True,
            "data": history
        }
    except Exception as e:
        logger.error(f"Failed to get purchase history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get purchase history: {str(e)}")


@router.post("/purchase")
async def record_purchase(purchase: PurchaseRecord):
    """Record a new Bitcoin purchase."""
    try:
        decision_maker_service.add_purchase_record(purchase)
        return {
            "success": True,
            "message": "Purchase recorded successfully",
            "purchase": purchase
        }
    except Exception as e:
        logger.error(f"Failed to record purchase: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record purchase: {str(e)}")


@router.get("/should-buy/{price}")
async def should_buy_at_price(price: float):
    """Check if should buy at given price."""
    try:
        decision = await decision_maker_service.should_make_purchase(price)
        return {
            "success": True,
            "decision": decision
        }
    except Exception as e:
        logger.error(f"Failed to evaluate purchase decision: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to evaluate purchase decision: {str(e)}")


@router.get("/config")
async def get_dca_config():
    """Get current DCA configuration."""
    try:
        config = decision_maker_service.get_dca_config()
        return {
            "success": True,
            "config": config
        }
    except Exception as e:
        logger.error(f"Failed to get DCA config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get DCA config: {str(e)}")


@router.put("/config")
async def update_dca_config(config: DCAConfig):
    """Update DCA configuration."""
    try:
        decision_maker_service.update_dca_config(config)
        return {
            "success": True,
            "message": "DCA configuration updated successfully",
            "config": config
        }
    except Exception as e:
        logger.error(f"Failed to update DCA config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update DCA config: {str(e)}")