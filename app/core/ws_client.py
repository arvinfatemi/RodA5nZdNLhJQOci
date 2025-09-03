import json
import logging
import threading
import time
from typing import Callable, Dict, List, Optional, Union

# Public Advanced Trade WebSocket endpoint
WS_URL = "wss://advanced-trade-ws.coinbase.com"

# Map flexible user inputs to Coinbase Advanced Trade candles granularity enums
GRANULARITY_MAP: Dict[Union[str, int], str] = {
    # strings
    "1m": "ONE_MINUTE",
    "5m": "FIVE_MINUTE",
    "15m": "FIFTEEN_MINUTE",
    "30m": "THIRTY_MINUTE",
    "1h": "ONE_HOUR",
    "1d": "ONE_DAY",
    # ints (seconds)
    60: "ONE_MINUTE",
    300: "FIVE_MINUTE",
    900: "FIFTEEN_MINUTE",
    1800: "THIRTY_MINUTE",
    3600: "ONE_HOUR",
    86400: "ONE_DAY",
}


def _resolve_granularity(granularity: Optional[Union[str, int]]) -> str:
    if granularity is None:
        return "THIRTY_MINUTE"
    if isinstance(granularity, str):
        g = granularity.strip().upper()
        # normalize common aliases
        alias = {
            "ONE_MINUTE": "ONE_MINUTE",
            "FIVE_MINUTE": "FIVE_MINUTE",
            "FIFTEEN_MINUTE": "FIFTEEN_MINUTE",
            "THIRTY_MINUTE": "THIRTY_MINUTE",
            "ONE_HOUR": "ONE_HOUR",
            "ONE_DAY": "ONE_DAY",
            "1M": "ONE_MINUTE",
            "5M": "FIVE_MINUTE",
            "15M": "FIFTEEN_MINUTE",
            "30M": "THIRTY_MINUTE",
            "1H": "ONE_HOUR",
            "1D": "ONE_DAY",
        }
        if g in alias:
            return alias[g]
        # support lower "Xm" strings via map
        return GRANULARITY_MAP.get(granularity, "THIRTY_MINUTE")
    return GRANULARITY_MAP.get(granularity, "THIRTY_MINUTE")


class CoinbaseWSClient:
    """Connects to Coinbase Advanced Trade WebSocket for public market data.

    Subscribes to ticker, candles, and heartbeat for provided products.
    Uses coinbase-advanced-py SDK if available; otherwise falls back to raw websocket-client.
    """

    def __init__(
        self,
        products: Optional[List[str]] = None,
        *,
        granularity: Optional[Union[str, int]] = "THIRTY_MINUTE",
        on_ticker: Optional[Callable[[Dict], None]] = None,
        on_candle: Optional[Callable[[Dict], None]] = None,
        on_heartbeat: Optional[Callable[[Dict], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        logger: Optional[logging.Logger] = None,
        use_sdk_preferred: bool = True,
    ) -> None:
        self.products = products or ["BTC-USD"]
        self.granularity = _resolve_granularity(granularity)
        self.on_ticker = on_ticker
        self.on_candle = on_candle
        self.on_heartbeat = on_heartbeat
        self.on_error = on_error
        self.log = logger or logging.getLogger("coinbase_ws")
        self.use_sdk_preferred = use_sdk_preferred

        self._sdk_client = None
        self._ws = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------- Public API -------------
    def start(self) -> None:
        """Start the WebSocket connection in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="coinbase-ws", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        """Request shutdown and wait up to timeout seconds."""
        self._stop_event.set()
        try:
            if self._ws:
                try:
                    # Hint the raw WebSocketApp loop to stop
                    if hasattr(self._ws, "keep_running"):
                        setattr(self._ws, "keep_running", False)
                except Exception:
                    pass
                try:
                    self._ws.close()
                except Exception:
                    pass
            if self._sdk_client:
                try:
                    # Ask SDK client to close gracefully
                    self._sdk_client.close()
                except Exception:
                    pass
                # As a fallback, force-stop the SDK event loop/thread if still present
                try:
                    loop = getattr(self._sdk_client, "loop", None)
                    if loop:
                        try:
                            loop.call_soon_threadsafe(loop.stop)
                        except Exception:
                            pass
                    th = getattr(self._sdk_client, "thread", None)
                    if th:
                        th.join(timeout=timeout)
                except Exception:
                    pass
        finally:
            if self._thread:
                self._thread.join(timeout=timeout)

    # ------------- Internal -------------
    def _run(self) -> None:
        # Try SDK first if requested
        if self.use_sdk_preferred and self._try_run_sdk():
            return
        # Fallback to raw websocket-client
        self._run_raw_ws()

    # SDK path
    def _try_run_sdk(self) -> bool:
        try:
            from coinbase.websocket import WSClient as CBWSClient  # type: ignore
        except Exception as e:
            self.log.info(f"coinbase-advanced-py SDK not available or import failed: {e}")
            return False

        products = list(self.products)

        def _on_message(msg: str) -> None:
            try:
                data = json.loads(msg)
            except Exception:
                self.log.debug("Received non-JSON SDK message")
                return
            self._route_message(data)

        def _on_open() -> None:
            self.log.info("SDK WS open; subscribing channels")
            try:
                # Subscribe using SDK-provided helpers bound on WSClient
                self._sdk_client.ticker(products)
                self._sdk_client.candles(products)
                self._sdk_client.heartbeats()
                if self.granularity != "THIRTY_MINUTE":
                    # SDK does not expose granularity selection; will use default (likely 1m).
                    # Consider local aggregation if needed.
                    pass
            except Exception as e:
                self.log.error(f"SDK subscribe failed: {e}")

        try:
            # Disable auto-retries so we can close cleanly
            self._sdk_client = CBWSClient(on_message=_on_message, on_open=_on_open, retry=False)
            self._sdk_client.open()
            # Block loop until stop
            while not self._stop_event.is_set():
                time.sleep(0.2)
            return True
        except Exception as e:
            self.log.info(f"SDK path failed, falling back to raw WS: {e}")
            try:
                if self._sdk_client:
                    self._sdk_client.close()
            except Exception:
                pass
            self._sdk_client = None
            return False

    # Raw websocket path
    def _run_raw_ws(self) -> None:
        try:
            import websocket  # type: ignore
        except Exception as e:
            self.log.error(
                f"websocket-client not installed. Install with: pip install websocket-client. Error: {e}"
            )
            if self.on_error:
                try:
                    self.on_error(e)
                except Exception:
                    pass
            return

        products = list(self.products)
        gran = self.granularity

        # Advanced Trade expects single-channel subscribe messages with a 'channel' field
        subscribe_msgs = [
            json.dumps({
                "type": "subscribe",
                "product_ids": products,
                "channel": "ticker",
            }),
            json.dumps({
                "type": "subscribe",
                "product_ids": products,
                "channel": "candles",
                "granularity": gran,
            }),
            json.dumps({
                "type": "subscribe",
                "product_ids": [],  # heartbeats is a global channel
                "channel": "heartbeats",
            }),
        ]

        def _on_open(ws):
            self.log.info("WS open; subscribing channels")
            try:
                for msg in subscribe_msgs:
                    ws.send(msg)
            except Exception as e:
                self.log.error(f"Subscribe send failed: {e}")

        def _on_message(ws, message):
            try:
                data = json.loads(message)
            except Exception:
                self.log.debug("Received non-JSON message")
                return
            self._route_message(data)

        def _on_error(ws, error):
            self.log.error(f"WS error: {error}")
            if self.on_error:
                try:
                    self.on_error(error)
                except Exception:
                    pass

        def _on_close(ws, status, msg):
            self.log.info(f"WS closed: {status} {msg}")

        self._ws = websocket.WebSocketApp(
            WS_URL,
            on_open=_on_open,
            on_message=_on_message,
            on_error=_on_error,
            on_close=_on_close,
        )

        # Run until stop requested
        while not self._stop_event.is_set():
            try:
                self._ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as e:
                self.log.warning(f"WS run_forever error, will retry in 3s: {e}")
                time.sleep(3)
            # If stop requested, exit loop
            if self._stop_event.is_set():
                break
            # Brief backoff before reconnect
            time.sleep(1)

    # Message routing
    def _route_message(self, data: Dict) -> None:
        # Advanced Trade messages typically include a channel identifier.
        channel = data.get("channel") or data.get("type")

        if channel == "ticker" or channel == "ticker_batch":
            if self.on_ticker:
                try:
                    self.on_ticker(data)
                except Exception:
                    pass
            return

        if channel == "candles" or channel == "candle":
            if self.on_candle:
                try:
                    self.on_candle(data)
                except Exception:
                    pass
            return

        if channel in ("heartbeat", "heartbeats"):
            if self.on_heartbeat:
                try:
                    self.on_heartbeat(data)
                except Exception:
                    pass
            return

        # Log errors and subscription confirmations to help debugging
        if channel in ("subscriptions", "error"):
            self.log.info(f"WS meta message on channel={channel}: {data}")
        else:
            # Other channels or unknown messages at debug level
            self.log.debug(f"Unhandled message on channel={channel}: {data}")


def connect_coinbase_ws(
    *,
    products: Optional[List[str]] = None,
    granularity: Optional[Union[str, int]] = "THIRTY_MINUTE",
    on_ticker: Optional[Callable[[Dict], None]] = None,
    on_candle: Optional[Callable[[Dict], None]] = None,
    on_heartbeat: Optional[Callable[[Dict], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
    logger: Optional[logging.Logger] = None,
    use_sdk_preferred: bool = True,
) -> CoinbaseWSClient:
    """Convenience function to create and start the Coinbase WS client.

    - Subscribes to ticker, candles (with specified granularity), and heartbeat.
    - Defaults to BTC-USD and THIRTY_MINUTE candles.
    - Returns the client so callers can stop it later via client.stop().
    """
    client = CoinbaseWSClient(
        products=products or ["BTC-USD"],
        granularity=granularity,
        on_ticker=on_ticker,
        on_candle=on_candle,
        on_heartbeat=on_heartbeat,
        on_error=on_error,
        logger=logger,
        use_sdk_preferred=use_sdk_preferred,
    )
    client.start()
    return client
