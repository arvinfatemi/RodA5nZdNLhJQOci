"""
API endpoints for advanced metrics and technical analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models.metrics import MetricsSnapshot, OnChainMetrics
from app.services.metrics_calculation_service import metrics_calculation_service
from app.services.onchain_metrics_service import onchain_metrics_service
from app.services.decision_maker_service import decision_maker_service

logger = logging.getLogger(__name__)

router = APIRouter()


class MetricsResponse(BaseModel):
    """Response model for metrics endpoints."""

    success: bool
    data: Dict[str, Any]
    timestamp: datetime


@router.get("/snapshot", response_model=MetricsResponse)
async def get_metrics_snapshot():
    """Get a complete metrics snapshot with technical indicators."""
    try:
        snapshot = await metrics_calculation_service.get_metrics_snapshot()
        
        return MetricsResponse(
            success=True,
            data={
                "snapshot": snapshot.dict(),
                "data_quality": {
                    "completeness": snapshot.data_completeness,
                    "errors": snapshot.calculation_errors or [],
                    "last_updated": snapshot.timestamp
                }
            },
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error getting metrics snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technical-indicators")
async def get_technical_indicators():
    """Get current technical indicators."""
    try:
        snapshot = await metrics_calculation_service.get_metrics_snapshot()
        
        return {
            "success": True,
            "data": {
                "indicators": snapshot.technical_indicators.dict(),
                "current_price": snapshot.current_price,
                "timestamp": snapshot.timestamp,
                "market_context": snapshot.market_context.dict() if snapshot.market_context else None
            }
        }

    except Exception as e:
        logger.error(f"Error getting technical indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/onchain")
async def get_onchain_metrics():
    """Get Bitcoin on-chain metrics."""
    try:
        onchain_metrics = await onchain_metrics_service.get_onchain_metrics()
        network_health = await onchain_metrics_service.get_network_health_score()
        fear_greed = await onchain_metrics_service.get_fear_greed_index()
        
        return {
            "success": True,
            "data": {
                "onchain_metrics": onchain_metrics.dict(),
                "network_health": network_health,
                "fear_greed_index": fear_greed,
                "timestamp": datetime.now()
            }
        }

    except Exception as e:
        logger.error(f"Error getting on-chain metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-analysis")
async def get_risk_analysis():
    """Get portfolio risk metrics and analysis."""
    try:
        snapshot = await metrics_calculation_service.get_metrics_snapshot()
        
        # Get historical price data for risk calculations
        from app.services.bitcoin_service import bitcoin_service
        candles_response = await bitcoin_service.get_bitcoin_candles(hours=24*30, granularity="ONE_DAY")  # 30 days
        
        if candles_response["success"]:
            prices = [candle["close"] for candle in candles_response["data"]["candles"]]
            risk_metrics = await metrics_calculation_service.calculate_risk_metrics(prices)
        else:
            risk_metrics = None

        return {
            "success": True,
            "data": {
                "risk_metrics": risk_metrics.dict() if risk_metrics else None,
                "current_volatility": snapshot.technical_indicators.volatility_7d,
                "atr_analysis": {
                    "atr_14": snapshot.technical_indicators.atr_14,
                    "atr_percentage": (snapshot.technical_indicators.atr_14 / snapshot.current_price * 100) 
                                    if snapshot.technical_indicators.atr_14 and snapshot.current_price else None
                },
                "timestamp": datetime.now()
            }
        }

    except Exception as e:
        logger.error(f"Error getting risk analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-analysis")
async def get_market_analysis():
    """Get comprehensive market analysis with metrics."""
    try:
        # Get enhanced market evaluation
        market_evaluation = await decision_maker_service.evaluate_market_with_metrics()
        
        return {
            "success": True,
            "data": {
                "basic_decision": market_evaluation["basic_decision"].dict(),
                "enhanced_decision": market_evaluation["enhanced_decision"].dict(),
                "market_analysis": market_evaluation.get("market_analysis", {}),
                "metrics_summary": {
                    "technical_indicators": market_evaluation.get("metrics_snapshot", {}).technical_indicators.dict() 
                                          if market_evaluation.get("metrics_snapshot") else None,
                    "market_context": market_evaluation.get("metrics_snapshot", {}).market_context.dict() 
                                    if market_evaluation.get("metrics_snapshot") and market_evaluation["metrics_snapshot"].market_context else None,
                    "network_health": market_evaluation.get("network_health", {}),
                    "fear_greed_index": market_evaluation.get("fear_greed_index")
                },
                "timestamp": datetime.now()
            }
        }

    except Exception as e:
        logger.error(f"Error getting market analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/atr-stop-loss")
async def calculate_atr_stop_loss(
    entry_price: float = Query(..., description="Entry price for the trade"),
    atr_multiplier: float = Query(1.5, description="ATR multiplier for stop loss calculation")
):
    """Calculate ATR-based stop loss levels."""
    try:
        snapshot = await metrics_calculation_service.get_metrics_snapshot()
        
        if not snapshot.technical_indicators.atr_14:
            raise HTTPException(status_code=400, detail="ATR data not available")
        
        from app.models.metrics import ATRConfig
        atr_config = ATRConfig(atr_multiplier=atr_multiplier)
        
        stop_loss_price, stop_loss_percentage = metrics_calculation_service.calculate_atr_stop_loss(
            entry_price, snapshot.technical_indicators.atr_14, atr_config
        )
        
        return {
            "success": True,
            "data": {
                "entry_price": entry_price,
                "atr_14": snapshot.technical_indicators.atr_14,
                "atr_multiplier": atr_multiplier,
                "stop_loss_price": stop_loss_price,
                "stop_loss_percentage": stop_loss_percentage,
                "risk_amount": entry_price - stop_loss_price,
                "current_price": snapshot.current_price,
                "timestamp": datetime.now()
            }
        }

    except Exception as e:
        logger.error(f"Error calculating ATR stop loss: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/volatility-analysis")
async def get_volatility_analysis():
    """Get detailed volatility analysis."""
    try:
        snapshot = await metrics_calculation_service.get_metrics_snapshot()
        
        volatility_data = {
            "atr_14": snapshot.technical_indicators.atr_14,
            "volatility_7d": snapshot.technical_indicators.volatility_7d,
            "current_price": snapshot.current_price
        }
        
        # Calculate volatility percentages
        analysis = {}
        if snapshot.technical_indicators.atr_14 and snapshot.current_price:
            atr_percentage = (snapshot.technical_indicators.atr_14 / snapshot.current_price) * 100
            analysis["atr_percentage"] = atr_percentage
            
            if atr_percentage > 5:
                analysis["volatility_regime"] = "high"
            elif atr_percentage > 2:
                analysis["volatility_regime"] = "medium"  
            else:
                analysis["volatility_regime"] = "low"
        
        if snapshot.technical_indicators.volatility_7d:
            vol_percentage = snapshot.technical_indicators.volatility_7d * 100
            analysis["daily_volatility_percentage"] = vol_percentage
        
        return {
            "success": True,
            "data": {
                "volatility_metrics": volatility_data,
                "volatility_analysis": analysis,
                "market_context": snapshot.market_context.dict() if snapshot.market_context else None,
                "timestamp": datetime.now()
            }
        }

    except Exception as e:
        logger.error(f"Error getting volatility analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/support-resistance")
async def get_support_resistance_levels():
    """Get current support and resistance levels."""
    try:
        snapshot = await metrics_calculation_service.get_metrics_snapshot()
        
        if not snapshot.market_context:
            raise HTTPException(status_code=400, detail="Market context data not available")
        
        current_price = snapshot.current_price
        support_levels = snapshot.market_context.support_levels or []
        resistance_levels = snapshot.market_context.resistance_levels or []
        
        # Find nearest levels
        nearest_support = max([level for level in support_levels if level < current_price], default=None)
        nearest_resistance = min([level for level in resistance_levels if level > current_price], default=None)
        
        return {
            "success": True,
            "data": {
                "current_price": current_price,
                "support_levels": support_levels,
                "resistance_levels": resistance_levels,
                "nearest_support": nearest_support,
                "nearest_resistance": nearest_resistance,
                "support_distance": ((current_price - nearest_support) / current_price * 100) if nearest_support else None,
                "resistance_distance": ((nearest_resistance - current_price) / current_price * 100) if nearest_resistance else None,
                "timestamp": datetime.now()
            }
        }

    except Exception as e:
        logger.error(f"Error getting support/resistance levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend-analysis")
async def get_trend_analysis():
    """Get multi-timeframe trend analysis."""
    try:
        snapshot = await metrics_calculation_service.get_metrics_snapshot()
        
        if not snapshot.market_context:
            raise HTTPException(status_code=400, detail="Market context data not available")
        
        # Get moving averages for trend confirmation
        indicators = snapshot.technical_indicators
        current_price = snapshot.current_price
        
        trend_data = {
            "short_term_trend": snapshot.market_context.short_term_trend,
            "medium_term_trend": snapshot.market_context.medium_term_trend,
            "long_term_trend": snapshot.market_context.long_term_trend,
            "current_price": current_price,
            "sma_20": indicators.sma_20,
            "sma_50": indicators.sma_50,
            "sma_200": indicators.sma_200
        }
        
        # Analyze trend strength
        trend_strength = "weak"
        if (indicators.sma_20 and indicators.sma_50 and indicators.sma_200 and
            current_price > indicators.sma_20 > indicators.sma_50 > indicators.sma_200):
            trend_strength = "strong_bullish"
        elif (indicators.sma_20 and indicators.sma_50 and indicators.sma_200 and
              current_price < indicators.sma_20 < indicators.sma_50 < indicators.sma_200):
            trend_strength = "strong_bearish"
        elif indicators.sma_20 and current_price > indicators.sma_20:
            trend_strength = "moderate_bullish"
        elif indicators.sma_20 and current_price < indicators.sma_20:
            trend_strength = "moderate_bearish"
        
        return {
            "success": True,
            "data": {
                "trend_analysis": trend_data,
                "trend_strength": trend_strength,
                "market_regime": snapshot.market_context.market_regime,
                "timestamp": datetime.now()
            }
        }

    except Exception as e:
        logger.error(f"Error getting trend analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))