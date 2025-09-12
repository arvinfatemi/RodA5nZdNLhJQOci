"""
Service for fetching Bitcoin on-chain metrics from various blockchain data providers.
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.models.metrics import OnChainMetrics

logger = logging.getLogger(__name__)


class OnChainMetricsService:
    """Service for fetching Bitcoin blockchain and on-chain metrics."""

    def __init__(self):
        self.logger = logger
        self.cache: Dict[str, Any] = {}
        self.cache_timeout = timedelta(minutes=30)  # Cache for 30 minutes

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self.cache:
            return False
        
        cache_time = self.cache[key].get("timestamp")
        if not cache_time:
            return False
        
        return datetime.now() - cache_time < self.cache_timeout

    def _get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data if valid."""
        if self._is_cache_valid(key):
            return self.cache[key]["data"]
        return None

    def _set_cache(self, key: str, data: Dict[str, Any]):
        """Set cached data with timestamp."""
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now()
        }

    async def fetch_blockchain_info_metrics(self) -> Dict[str, Any]:
        """Fetch metrics from Blockchain.info API."""
        cache_key = "blockchain_info"
        cached = self._get_cached_data(cache_key)
        if cached:
            return cached

        try:
            # Blockchain.info stats API
            response = requests.get("https://blockchain.info/stats?format=json", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = {
                "hash_rate": data.get("hash_rate", 0) / 1e12,  # Convert to TH/s
                "difficulty": data.get("difficulty", 0),
                "total_bitcoins": data.get("totalbc", 0) / 1e8,  # Convert from satoshis
                "market_cap": data.get("market_price_usd", 0) * data.get("totalbc", 0) / 1e8,
                "blocks_size": data.get("blocks_size", 0),
                "n_tx": data.get("n_tx", 0),
            }
            
            self._set_cache(cache_key, result)
            return result

        except Exception as e:
            self.logger.warning(f"Failed to fetch blockchain.info metrics: {e}")
            return {}

    async def fetch_mempool_space_metrics(self) -> Dict[str, Any]:
        """Fetch metrics from Mempool.space API."""
        cache_key = "mempool_space"
        cached = self._get_cached_data(cache_key)
        if cached:
            return cached

        try:
            # Get mempool info
            mempool_response = requests.get("https://mempool.space/api/mempool", timeout=10)
            mempool_response.raise_for_status()
            mempool_data = mempool_response.json()
            
            # Get fees recommendation
            fees_response = requests.get("https://mempool.space/api/v1/fees/recommended", timeout=10)
            fees_response.raise_for_status()
            fees_data = fees_response.json()
            
            # Get latest block info
            blocks_response = requests.get("https://mempool.space/api/blocks", timeout=10)
            blocks_response.raise_for_status()
            blocks_data = blocks_response.json()
            
            latest_block = blocks_data[0] if blocks_data else {}
            
            result = {
                "mempool_size": mempool_data.get("count", 0),
                "mempool_vsize": mempool_data.get("vsize", 0),
                "mempool_total_fee": mempool_data.get("total_fee", 0),
                "fast_fee": fees_data.get("fastestFee", 0),
                "medium_fee": fees_data.get("halfHourFee", 0),
                "slow_fee": fees_data.get("hourFee", 0),
                "latest_block_height": latest_block.get("height", 0),
                "latest_block_size": latest_block.get("size", 0),
                "latest_block_tx_count": latest_block.get("tx_count", 0),
            }
            
            self._set_cache(cache_key, result)
            return result

        except Exception as e:
            self.logger.warning(f"Failed to fetch mempool.space metrics: {e}")
            return {}

    async def fetch_coinmetrics_data(self) -> Dict[str, Any]:
        """Fetch data from CoinMetrics (free tier)."""
        cache_key = "coinmetrics"
        cached = self._get_cached_data(cache_key)
        if cached:
            return cached

        try:
            # Note: This would require a CoinMetrics API key for full access
            # For now, we'll simulate or use publicly available endpoints
            
            # This is a placeholder - you would implement actual CoinMetrics API calls here
            result = {
                "active_addresses": None,  # Would require API key
                "transaction_volume": None,  # Would require API key
                "nvt_ratio": None,  # Network Value to Transactions ratio
            }
            
            self._set_cache(cache_key, result)
            return result

        except Exception as e:
            self.logger.warning(f"Failed to fetch CoinMetrics data: {e}")
            return {}

    async def fetch_bitinfocharts_metrics(self) -> Dict[str, Any]:
        """Fetch metrics from BitInfoCharts (via web scraping or API if available)."""
        cache_key = "bitinfocharts"
        cached = self._get_cached_data(cache_key)
        if cached:
            return cached

        try:
            # BitInfoCharts doesn't have a direct API, but we can approximate
            # some metrics or use alternative sources
            
            # This is a placeholder implementation
            result = {
                "avg_transaction_fee": None,  # Would need scraping or alternative API
                "avg_block_size": None,
                "transactions_per_day": None,
            }
            
            self._set_cache(cache_key, result)
            return result

        except Exception as e:
            self.logger.warning(f"Failed to fetch BitInfoCharts metrics: {e}")
            return {}

    async def calculate_derived_metrics(self, blockchain_data: Dict, mempool_data: Dict) -> Dict[str, Any]:
        """Calculate derived on-chain metrics from fetched data."""
        try:
            derived = {}
            
            # Calculate average transaction fee in USD (approximate)
            if mempool_data.get("mempool_total_fee") and mempool_data.get("mempool_size"):
                avg_fee_sats = mempool_data["mempool_total_fee"] / mempool_data["mempool_size"]
                # Convert to USD (would need current BTC price)
                # derived["avg_transaction_fee_usd"] = avg_fee_sats * btc_price / 1e8
            
            # Network congestion indicator
            if mempool_data.get("mempool_size"):
                if mempool_data["mempool_size"] > 50000:
                    derived["network_congestion"] = "high"
                elif mempool_data["mempool_size"] > 20000:
                    derived["network_congestion"] = "medium"
                else:
                    derived["network_congestion"] = "low"
            
            # Hash rate trend (would need historical data)
            derived["hash_rate_trend"] = "stable"  # Placeholder
            
            return derived

        except Exception as e:
            self.logger.warning(f"Failed to calculate derived metrics: {e}")
            return {}

    async def get_onchain_metrics(self) -> OnChainMetrics:
        """Get comprehensive on-chain metrics."""
        try:
            # Fetch data from multiple sources
            blockchain_data = await self.fetch_blockchain_info_metrics()
            mempool_data = await self.fetch_mempool_space_metrics()
            coinmetrics_data = await self.fetch_coinmetrics_data()
            bitinfo_data = await self.fetch_bitinfocharts_metrics()
            
            # Calculate derived metrics
            derived_data = await self.calculate_derived_metrics(blockchain_data, mempool_data)
            
            # Combine all data into OnChainMetrics model
            return OnChainMetrics(
                # Network metrics from blockchain.info
                hash_rate=blockchain_data.get("hash_rate"),
                difficulty=blockchain_data.get("difficulty"),
                block_height=mempool_data.get("latest_block_height"),
                mempool_size=mempool_data.get("mempool_size"),
                average_block_size=mempool_data.get("latest_block_size", 0) / 1024 / 1024 if mempool_data.get("latest_block_size") else None,  # Convert to MB
                
                # Transaction metrics
                transaction_count_24h=blockchain_data.get("n_tx"),
                average_transaction_fee=mempool_data.get("medium_fee"),  # in sat/vB
                
                # Market metrics
                market_cap=blockchain_data.get("market_cap"),
                circulating_supply=blockchain_data.get("total_bitcoins"),
                
                # Address activity (would need premium APIs)
                active_addresses=coinmetrics_data.get("active_addresses"),
                new_addresses=None,  # Would require premium data
                
                # Additional derived metrics could be added here
                median_transaction_value=None,  # Would require transaction-level data
            )

        except Exception as e:
            self.logger.error(f"Failed to get on-chain metrics: {e}")
            return OnChainMetrics()

    async def get_fear_greed_index(self) -> Optional[int]:
        """Get Fear & Greed Index from Alternative.me."""
        try:
            response = requests.get("https://api.alternative.me/fng/", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data") and len(data["data"]) > 0:
                return int(data["data"][0]["value"])
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch Fear & Greed Index: {e}")
        
        return None

    async def get_network_health_score(self) -> Dict[str, Any]:
        """Calculate a composite network health score."""
        try:
            metrics = await self.get_onchain_metrics()
            
            health_score = 100  # Start with perfect score
            health_factors = []
            
            # Hash rate factor (higher is better)
            if metrics.hash_rate:
                if metrics.hash_rate < 100:  # Less than 100 TH/s is concerning
                    health_score -= 20
                    health_factors.append("Low hash rate")
            
            # Mempool factor (lower is better for network health)
            if metrics.mempool_size:
                if metrics.mempool_size > 100000:
                    health_score -= 30
                    health_factors.append("High mempool congestion")
                elif metrics.mempool_size > 50000:
                    health_score -= 15
                    health_factors.append("Moderate mempool congestion")
            
            # Fee factor (lower is better for users)
            if metrics.average_transaction_fee:
                if metrics.average_transaction_fee > 50:  # High fees
                    health_score -= 20
                    health_factors.append("High transaction fees")
                elif metrics.average_transaction_fee > 20:
                    health_score -= 10
                    health_factors.append("Elevated transaction fees")
            
            # Ensure score doesn't go below 0
            health_score = max(0, health_score)
            
            return {
                "health_score": health_score,
                "health_factors": health_factors,
                "status": "healthy" if health_score > 80 else "moderate" if health_score > 50 else "poor"
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate network health score: {e}")
            return {"health_score": 50, "health_factors": ["Unable to calculate"], "status": "unknown"}


# Global service instance
onchain_metrics_service = OnChainMetricsService()