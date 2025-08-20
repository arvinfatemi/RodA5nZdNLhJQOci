# Project Status Summary

## Overview
- Phase 1 goals: read config from Google Sheet and stream Coinbase market data (ticker, candles, heartbeat) for `BTC-USD`.
- Implemented a configurable WebSocket client with SDK-first (optional) and raw fallback, plus CLI flags to test and verify data quickly.

## Repo Setup
- Initialized git and fixed `.gitignore` so secrets and artifacts are ignored: `.env`, `.env.*`, `service_account.json`, `config_cache.json`, `__pycache__/`, etc.

## Config Loading (Google Sheet)
- File: `config_loader.py`
  - Validates inline creds `GCP_SERVICE_ACCOUNT_JSON`; falls back to file path `GOOGLE_APPLICATION_CREDENTIALS`.
  - Detects and rejects OAuth client JSON mistakenly used as service account keys.
  - Caching supported (`config_cache.json`) with freshness checks; merges with defaults; provides `_meta` source tag.
- Note: Your current `service_account.json` was an OAuth client file. You can either:
  - Use OAuth (quickstart style: `credentials.json` + `token.json`), or
  - Create a proper Service Account key, share the sheet with its `client_email`, and point `GOOGLE_APPLICATION_CREDENTIALS` to it.

## Google OAuth Quickstart
- `quickstart.py` (Google sample) works with Installed App flow and produces `token.json`.
- We added optional OAuth support inside `config_loader` path later (via quickstart), but currently `read_app_config_from_sheet` still uses service account auth by default.

## .env Handling
- `.env` added; `main.py` loads `.env` (fallback `.env.txt`).
- Env precedence: does not override existing OS env by default (keeps `override=False`).

## Coinbase WebSocket Client
- File: `ws_client.py`
  - Subscribes to public channels: `ticker`, `candles`, `heartbeats` for products (default `BTC-USD`).
  - Granularity: accepts `"30m"` (default) or enum/seconds; raw backend sends the correct `granularity` field.
  - Backends:
    - SDK: uses `coinbase.websocket.WSClient` with `ticker()`, `candles()`, `heartbeats()` (does not accept granularity parameter; likely 1m candles).
    - Raw: uses `websocket-client`; sends one subscribe per channel with `channel` field (matches Advanced Trade docs). Handles `heartbeats` plural.
  - Lifecycle: background thread + `start()`/`stop()`; improved shutdown for both paths.

## Main CLI Runner
- File: `main.py`
  - Flags:
    - `--ws-only`: skip Google Sheet fetch.
    - `--ws-backend sdk|raw` (default `raw`).
    - `--granularity 30m|1m|...|seconds`.
    - `--verify-data`: wait for data then exit (see `--verify-timeout`, `--require-all`).
    - `--duration N`: auto-stop after N seconds (testing).
    - `--force-exit`: force process termination after stopping WS.
  - Prints incoming messages: `ticker:` (full), `candle:` (full), `heartbeat:` (concise fields).
  - Adds Windows-friendly `q + Enter` stop in interactive mode.

## Known Issues / Caveats
- SDK candles granularity: SDK doesn’t expose a granularity argument; likely emits 1m candles.
- SDK shutdown: some environments keep SDK threads alive; use `--duration`/`--force-exit` or `--ws-backend raw` for clean exits.
- Raw backend dependency: requires `websocket-client` (`pip install websocket-client`).
- Sheet ID in `main.py` is currently hardcoded (for quick testing). Should be sourced from `.env`/config.

## Quick Verification Commands
- Raw backend, verify any data within 15s (recommended):
  - `python main.py --ws-only --ws-backend raw --verify-data`
- Require all three channels (may need a longer timeout):
  - `python main.py --ws-only --ws-backend raw --verify-data --require-all --verify-timeout 30`
- SDK backend 15s run:
  - `python main.py --ws-only --ws-backend sdk --duration 15`

## Next Steps
- Config:
  - Un-hardcode Sheet ID; read from `.env` (`GOOGLE_SHEET_ID`) and re-enable that path in `main.py`.
  - Decide on Service Account vs OAuth and finalize one path. If OAuth: wire `credentials.json` + `token.json` into `config_loader` (Installed App flow) by default.
- WebSocket:
  - Add optional 1m→30m candle aggregation so SDK and raw produce the same effective granularity.
  - Add simple reconnection/backoff metrics and liveness checks.
- Docs:
  - Update README with WS test commands, `.env` keys, and credential setup instructions.
- Tests:
  - Lightweight unit tests for `_resolve_granularity` and ws subscribe payloads.

## Files Touched
- `.gitignore` (fixed ignores)
- `.env` (added)
- `config_loader.py` (credential validation, error clarity)
- `main.py` (CLI, WS integration, verification, shutdown)
- `ws_client.py` (WS client with SDK/raw backends)
- `tools/check_coinbase_sdk.py`, `tools/inspect_coinbase_ws.py` (diagnostics)
- `quickstart.py` (Google sample, unmodified)

