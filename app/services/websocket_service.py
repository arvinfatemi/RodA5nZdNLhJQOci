"""
Service layer for WebSocket management.
"""

import json
import logging
from typing import Optional, Dict, Any

from app.core.ws_client import connect_coinbase_ws, CoinbaseWSClient

logger = logging.getLogger(__name__)


class WebSocketService:
    """Service for managing Coinbase WebSocket connections."""

    def __init__(self):
        self.logger = logger
        self.client_instance: Optional[CoinbaseWSClient] = None
        self.data_storage: Dict[str, Optional[Dict[str, Any]]] = {
            "ticker": None,
            "candle": None,
            "heartbeat": None,
        }

    def _on_ticker(self, msg: dict):
        """Handle ticker messages."""
        self.data_storage["ticker"] = msg
        self.logger.info(f"Received ticker: {json.dumps(msg, separators=(',', ':'))}")

    def _on_candle(self, msg: dict):
        """Handle candle messages."""
        self.data_storage["candle"] = msg
        self.logger.info(f"Received candle: {json.dumps(msg, separators=(',', ':'))}")

    def _on_heartbeat(self, msg: dict):
        """Handle heartbeat messages."""
        self.data_storage["heartbeat"] = msg
        self.logger.info(
            f"Received heartbeat: {json.dumps({k: msg.get(k) for k in ('channel', 'product_id', 'time', 'sequence')}, separators=(',', ':'))}"
        )

    async def start_websocket(self) -> Dict[str, Any]:
        """Start WebSocket connection."""
        if (
            self.client_instance
            and hasattr(self.client_instance, "_thread")
            and self.client_instance._thread
            and self.client_instance._thread.is_alive()
        ):
            return {"success": True, "message": "WebSocket is already running"}

        try:
            self.client_instance = connect_coinbase_ws(
                products=["BTC-USD"],
                granularity="30m",
                on_ticker=self._on_ticker,
                on_candle=self._on_candle,
                on_heartbeat=self._on_heartbeat,
                use_sdk_preferred=False,
            )

            return {
                "success": True,
                "message": "WebSocket connection started successfully",
            }

        except Exception as e:
            self.logger.error(f"Failed to start WebSocket: {e}")
            raise Exception(f"Failed to start WebSocket: {str(e)}")

    async def stop_websocket(self) -> Dict[str, Any]:
        """Stop WebSocket connection."""
        if not self.client_instance:
            return {"success": True, "message": "WebSocket is not running"}

        try:
            self.client_instance.stop()
            self.client_instance = None

            # Clear stored data
            for key in self.data_storage:
                self.data_storage[key] = None

            return {
                "success": True,
                "message": "WebSocket connection stopped successfully",
            }

        except Exception as e:
            self.logger.error(f"Failed to stop WebSocket: {e}")
            raise Exception(f"Failed to stop WebSocket: {str(e)}")

    async def get_websocket_status(self) -> Dict[str, Any]:
        """Get WebSocket connection status and latest data."""
        is_running = (
            self.client_instance is not None
            and hasattr(self.client_instance, "_thread")
            and self.client_instance._thread is not None
            and self.client_instance._thread.is_alive()
        )

        return {"is_running": is_running, "latest_data": self.data_storage}


# Global service instance
websocket_service = WebSocketService()
