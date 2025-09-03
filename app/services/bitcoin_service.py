"""
Service layer for Bitcoin price and candles data.
"""
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any

# Try to import Coinbase SDK
try:
    from coinbase.rest import RESTClient
    COINBASE_SDK_AVAILABLE = True
except ImportError:
    COINBASE_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


class BitcoinService:
    """Service for fetching Bitcoin price and candles data."""
    
    def __init__(self):
        self.logger = logger

    async def get_bitcoin_price(self) -> Dict[str, Any]:
        """Get current Bitcoin price using Coinbase SDK or public API."""
        if not COINBASE_SDK_AVAILABLE:
            raise Exception("Coinbase Advanced Python SDK not available. Install with: pip install coinbase-advanced-py")
        
        try:
            # Try authenticated client first (if API keys are available)
            try:
                client = RESTClient()
                # Test if we can access authenticated endpoints
                ticker = client.get_product_ticker("BTC-USD")
                product = client.get_product("BTC-USD")
                
                result = {
                    "product_id": "BTC-USD",
                    "current_price": float(ticker.price) if ticker.price else None,
                    "price_24h_change": float(ticker.price_percentage_change_24h) if ticker.price_percentage_change_24h else None,
                    "volume_24h": float(ticker.volume_24h) if ticker.volume_24h else None,
                    "market_cap": float(ticker.market_cap) if hasattr(ticker, 'market_cap') and ticker.market_cap else None,
                    "bid": float(ticker.best_bid) if ticker.best_bid else None,
                    "ask": float(ticker.best_ask) if ticker.best_ask else None,
                    "timestamp": datetime.now().isoformat(),
                    "source": "coinbase_sdk_authenticated",
                    "product_info": {
                        "display_name": product.display_name if hasattr(product, 'display_name') else None,
                        "status": product.status if hasattr(product, 'status') else None,
                        "base_currency": product.base_currency_id if hasattr(product, 'base_currency_id') else None,
                        "quote_currency": product.quote_currency_id if hasattr(product, 'quote_currency_id') else None,
                    }
                }
                
                return {"success": True, "data": result}
                
            except Exception as auth_error:
                # Fall back to public API using requests
                self.logger.info(f"Authenticated API failed, falling back to public API: {auth_error}")
                
                # Use Coinbase Pro public API (which is still accessible)
                try:
                    # Get ticker data from public API
                    ticker_response = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/ticker")
                    ticker_response.raise_for_status()
                    ticker_data = ticker_response.json()
                    
                    # Get 24h stats
                    stats_response = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/stats")
                    stats_response.raise_for_status()
                    stats_data = stats_response.json()
                    
                    result = {
                        "product_id": "BTC-USD",
                        "current_price": float(ticker_data.get("price", 0)),
                        "bid": float(ticker_data.get("bid", 0)) if ticker_data.get("bid") else None,
                        "ask": float(ticker_data.get("ask", 0)) if ticker_data.get("ask") else None,
                        "volume_24h": float(ticker_data.get("volume", 0)) if ticker_data.get("volume") else None,
                        "price_24h_change": None,  # Calculate from stats if needed
                        "high_24h": float(stats_data.get("high", 0)) if stats_data.get("high") else None,
                        "low_24h": float(stats_data.get("low", 0)) if stats_data.get("low") else None,
                        "open_24h": float(stats_data.get("open", 0)) if stats_data.get("open") else None,
                        "last_24h": float(stats_data.get("last", 0)) if stats_data.get("last") else None,
                        "timestamp": datetime.now().isoformat(),
                        "source": "coinbase_public_api",
                    }
                    
                    # Calculate 24h change percentage if we have open price
                    if result["open_24h"] and result["current_price"]:
                        result["price_24h_change"] = ((result["current_price"] - result["open_24h"]) / result["open_24h"]) * 100
                    
                    return {"success": True, "data": result}
                    
                except Exception as public_error:
                    raise Exception(f"Both authenticated and public API failed. Auth error: {auth_error}. Public error: {public_error}")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch Bitcoin price: {e}")
            raise Exception(f"Failed to fetch Bitcoin price: {str(e)}")

    async def get_bitcoin_candles(self, hours: int = 24, granularity: str = "ONE_HOUR") -> Dict[str, Any]:
        """Get Bitcoin candle data using Coinbase SDK or public API."""
        if not COINBASE_SDK_AVAILABLE:
            raise Exception("Coinbase Advanced Python SDK not available. Install with: pip install coinbase-advanced-py")
        
        try:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            try:
                # Try authenticated SDK first
                client = RESTClient()
                
                # Get candles data
                candles = client.get_candles(
                    product_id="BTC-USD",
                    start=start_time.isoformat(),
                    end=end_time.isoformat(),
                    granularity=granularity
                )
                
                # Convert candles to readable format
                candles_data = []
                for candle in candles:
                    candles_data.append({
                        "timestamp": candle.start,
                        "low": float(candle.low),
                        "high": float(candle.high),
                        "open": float(candle.open),
                        "close": float(candle.close),
                        "volume": float(candle.volume)
                    })
                
                # Sort by timestamp (most recent first)
                candles_data.sort(key=lambda x: x["timestamp"], reverse=True)
                
                result = {
                    "product_id": "BTC-USD",
                    "granularity": granularity,
                    "hours_requested": hours,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "candles_count": len(candles_data),
                    "source": "coinbase_sdk_authenticated",
                    "candles": candles_data[:50]  # Limit to first 50 for web display
                }
                
                return {"success": True, "data": result}
                
            except Exception as auth_error:
                # Fall back to public API
                self.logger.info(f"Authenticated candles API failed, falling back to public API: {auth_error}")
                
                # Map granularity to seconds for public API
                granularity_seconds = {
                    "ONE_MINUTE": 60,
                    "FIVE_MINUTE": 300,
                    "FIFTEEN_MINUTE": 900,
                    "THIRTY_MINUTE": 1800,
                    "ONE_HOUR": 3600,
                    "SIX_HOUR": 21600,
                    "ONE_DAY": 86400
                }
                
                granularity_sec = granularity_seconds.get(granularity, 3600)  # Default to 1 hour
                
                # Use Coinbase Pro public API for candles
                params = {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "granularity": granularity_sec
                }
                
                candles_response = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/candles", params=params)
                candles_response.raise_for_status()
                candles_raw = candles_response.json()
                
                # Convert to our format (public API returns [timestamp, low, high, open, close, volume])
                candles_data = []
                for candle in candles_raw:
                    if len(candle) >= 6:
                        candles_data.append({
                            "timestamp": datetime.fromtimestamp(candle[0]).isoformat() + "Z",
                            "low": float(candle[1]),
                            "high": float(candle[2]),
                            "open": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": float(candle[5])
                        })
                
                # Sort by timestamp (most recent first)
                candles_data.sort(key=lambda x: x["timestamp"], reverse=True)
                
                result = {
                    "product_id": "BTC-USD",
                    "granularity": granularity,
                    "granularity_seconds": granularity_sec,
                    "hours_requested": hours,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "candles_count": len(candles_data),
                    "source": "coinbase_public_api",
                    "candles": candles_data[:50]  # Limit to first 50 for web display
                }
                
                return {"success": True, "data": result}
            
        except Exception as e:
            self.logger.error(f"Failed to fetch Bitcoin candles: {e}")
            raise Exception(f"Failed to fetch Bitcoin candles: {str(e)}")


# Global service instance
bitcoin_service = BitcoinService()