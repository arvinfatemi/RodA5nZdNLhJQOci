# BTC Trading Bot – Codebase Overview

This document summarizes the architecture, flow, and key modules of the project.

## High‑Level Architecture

- FastAPI web app exposing a REST API and a small dashboard UI
- Google Sheets‑backed configuration with local JSON caching
- Market data via Coinbase (SDK when available; public REST/WS fallback)
- Trading logic using a DCA baseline enhanced with technical/on‑chain metrics
- Simulated trades, Telegram notifications, and JSON persistence for state/history

Primary runtime uses the modular app under `app/` (v2). Some legacy utilities exist at the repo root for manual testing and backwards compatibility.

## Runtime Flow

1. App starts (`app/main.py`), mounts API at `/api/v1`, serves dashboard at `/`.
2. Lifespan hook starts the background scheduler (`scheduler_service`) using interval from config (default 30m).
3. Each scheduled run:
   - Loads config (Google Sheet → cache → defaults) via `config_service`.
   - Pulls market data and computes metrics.
   - Produces a trading decision (DCA threshold) with enhanced context.
   - Executes a simulated trade (if applicable), persists logs, sends Telegram notifications.
4. Shutdown stops the scheduler and any WS client.

## Key Modules and Responsibilities

### Models (`app/models/*`)
- `trading.py`: `DCAConfig`, `PurchaseRecord`, `TradingDecision`, `SimulatedTrade`, `TradingBotStatus`.
- `metrics.py`: `CandleData`, `TechnicalIndicators`, `RiskMetrics`, `MarketContext`, `MetricsSnapshot`.
- `bitcoin.py`, `websocket.py`, `config.py`: Pydantic response schemas.

### Services (`app/services/*`)
- `config_service.py`: Loads app config from Google Sheets via core loader.
- `bitcoin_service.py`: Current price and candles. Prefers Coinbase SDK; falls back to public REST.
- `metrics_calculation_service.py`: RSI/SMA/EMA/ATR/Bollinger, drawdown/VAR/Sharpe, market context, ATR stop loss; returns `MetricsSnapshot`.
- `onchain_metrics_service.py`: blockchain.info, mempool.space, Alternative.me (Fear & Greed), with simple caching and derived indicators.
- `decision_maker_service.py`: DCA decision; caches config for ~30 min; in‑memory purchase history; returns basic and enhanced decisions using metrics.
- `simulated_trading_service.py`: Executes simulated buys, writes to `simulated_trades.json`, exports CSV, daily counters.
- `scheduler_service.py`: APScheduler AsyncIO jobs for periodic checks, daily reset, and weekly email reports; updates persistent state; triggers notifications.
- `report_service.py`: Generates weekly email reports with trading performance, portfolio summary, and market analysis.
- `notification_service.py`: Formats and sends Telegram messages; persists success/fail history.
- `persistent_storage_service.py`: `bot_state.json` and `notification_history.json` management, cleanup, export.
- `telegram_service.py`: Wraps `app/core/telegram_notifier.py` to send and auto‑resolve chat id.
- `websocket_service.py`: Manages Coinbase WS client; stores last ticker/candle/heartbeat.

### Core (`app/core/*`)
- `config_loader.py`: Reads/validates Google Sheet; merges defaults; caches to JSON; supports service account, OAuth, or public CSV fallback.
- `ws_client.py`: Robust Coinbase WS client. Uses coinbase SDK if available; else raw `websocket-client`. Subscribes to ticker/candles/heartbeat with reconnect.
- `telegram_notifier.py`: Minimal dependency Telegram sender; can resolve and persist `TELEGRAM_CHAT_ID` to `.env`.
- `email_notifier.py`: SMTP-based email notification with HTML support for weekly reports.

### API Surface (`/api/v1`)
- Aggregation: `app/api/api_v1/api.py`.
- `config`: `GET /config` – Google Sheet config (+ `_meta`).
- `websocket`: `POST /websocket/start|stop`, `GET /websocket/status`.
- `telegram`: `POST /telegram/send` – send a Telegram message.
- `bitcoin`: `GET /bitcoin/price`, `GET /bitcoin/candles?hours&granularity`.
- `trading`: `GET /trading/decision`, `GET /trading/history`, `POST /trading/purchase`, `GET /trading/should-buy/{price}`, `GET /trading/config`.
- `bot`: `GET /bot/status`, `POST /bot/start`, `POST /bot/stop`, `POST /bot/check`, `GET /bot/history`, `GET /bot/summary`, `POST /bot/export/csv`.
- `metrics`: `GET /metrics/snapshot`, `/technical-indicators`, `/onchain`, `/risk-analysis`, `/market-analysis`, `/atr-stop-loss`.
- `reports`: `POST /reports/weekly/send`, `GET /reports/weekly/preview`, `GET /reports/weekly/html`, `GET /reports/config` – Weekly email reports.

## Configuration and Google Sheets

Loader: `app/core/config_loader.py`

- Sheet format (worksheet "Config" by default):
  `key | value | type | notes` (type ∈ int|float|bool|str|enum)
- Validates enums (e.g., `mode`, `report_day`) and casts values.
- Auth priority:
  1) `GCP_SERVICE_ACCOUNT_JSON` inline JSON (service account)
  2) `GOOGLE_APPLICATION_CREDENTIALS` path (service account or OAuth client secrets)
  3) `GOOGLE_OAUTH_CLIENT_SECRETS` or `./credentials.json` (Installed App flow with token cache)
  4) Public CSV export fallback (no auth required - perfect for learning)
- Cache strategy: fresh cache → live sheet → stale cache → defaults.

**For setup details, see**:
- [Simple Setup](SIMPLE_SETUP.md) - Public sheets, no authentication
- [Advanced Setup](ADVANCED_SETUP.md) - Private sheets with authentication

App settings (`app/config.py`) read `.env` for sheet IDs, telegram, ports, etc.

## Web Dashboard

- Templates: `app/templates/base.html`, `index.html`
- JS: `app/static/js/dashboard.js` (calls API for config, WS control, Telegram, price/candles, decision + notify)
- CSS: `app/static/css/style.css`

## Persistence and Data Files

- `config_cache.json`: cached sheet config
- `bot_state.json`: uptime, daily/lifetime counters, resets, config changes
- `notification_history.json`: notification results and summary
- `simulated_trades.json`: trade decisions and executed simulations, with summary

## Running

Recommended:

```bash
python -m app.main
# Visit http://localhost:8000 (API docs at /docs)
```

Environment:
- Copy `.env.example` to `.env` and fill `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (or let the app resolve it), Google credentials, etc.

## Notes & Gotchas

- Real exchange orders are NOT executed; trades are simulated and logged.
- Coinbase SDK optional. Public REST/WS fallback still needs `websocket-client` for WS path.
- Decision logic is DCA‑oriented; thresholds and toggles can be controlled via the Google Sheet.
- Legacy v1 files remain at the repo root (`app.py`, `main.py`, `ws_client.py`, `telegram_notifier.py`, `config_loader.py`) for manual testing; the main app uses `app/` modules.

