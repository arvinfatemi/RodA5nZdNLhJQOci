# Smart Bitcoin Trading Bot

## Project Overview
This project builds a smart, mostly autonomous Bitcoin trading agent for continuous (24/7) operation in the cloud. It dynamically manages budget allocation, combines long‑term accumulation (DCA) with short‑term trading using ATR‑based risk controls, and can switch among strategies (day trading, swing trading, value investing). It sends Telegram notifications for each trade, with weekly email summaries planned. Configuration is parameterized and loaded from a Google Sheet with a local cache; sensitive credentials live in a local `.env` file.

Key objectives:
- Configurable trading budget (e.g., $1K–$100K)
- DCA accumulation on drops and/or at intervals
- ATR‑based stop‑loss for active trades; optional ATR‑informed opportunistic DCA
- Strategy switching and lightweight LLM‑assisted adaptation
- 24/7 operation, deployable to cloud
- Telegram notifications on each trade; weekly Gmail summary

---

## Phases

### Phase 1
- ~~Connect to Google Sheet and fetch config~~
- ~~Read market data from Coinbase Advanced Trade API – WebSocket~~
- ~~Send messages to Telegram~~
- Send weekly Gmail reports
- Read market data from Coinbase Advanced Trade API – REST

### Phase 2
- Orchestration (scheduling, health checks, component coordination)

---

## How To Run This Code

### 1) Configure
This project uses a Google Sheet for application configuration and a local `.env` for secrets. Do not commit secrets.

- .env (minimum for current features):
  ```
  # Telegram (required to send trade notifications)
  TELEGRAM_BOT_TOKEN=1234567890:ABCDEF-your-bot-token
  # Optional; can be auto-resolved via helper (see below)
  TELEGRAM_CHAT_ID=123456789

  # Google authentication (choose one)
  # 1) Service Account (recommended)
  GOOGLE_APPLICATION_CREDENTIALS=./service_account.json
  # or inline
  # GCP_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

  # 2) OAuth client secrets (optional alternative)
  # GOOGLE_OAUTH_CLIENT_SECRETS=./credentials.json
  # GOOGLE_OAUTH_TOKEN_PATH=./token.json

  # Optional runtime settings
  # GOOGLE_SHEET_ID=your_google_sheet_id
  # WORKSHEET_NAME=Config
  # COINBASE_CANDLES_GRANULARITY=30m
  ```

- Google Sheets config:
  - Create a sheet with worksheet `Config` (or set `WORKSHEET_NAME`).
  - Headers: `key, value, type, notes` (see `config_loader.py` for expected keys and defaults).
  - Service Account flow: create a GCP service account, generate a JSON key, share the sheet with its `client_email`, and set `GOOGLE_APPLICATION_CREDENTIALS` (or `GCP_SERVICE_ACCOUNT_JSON`).
  - OAuth flow (alternative): provide `credentials.json`; first run will create `token.json`.

- Telegram setup:
  - Create a bot via BotFather to get `TELEGRAM_BOT_TOKEN`.
  - To resolve `TELEGRAM_CHAT_ID` automatically:
    - Send a message to your bot (or add it to the target group/channel and post a message).
    - Run: `python telegram_notifier.py --resolve-chat-id --env-path .env`
    - Test: `python telegram_notifier.py --text "Hello" --env-path .env`

### 2) Install Packages
Use a virtual environment and install requirements:
```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3) Run Locally (Phase 1 checks)
- Verify WebSocket (raw backend) delivers any data in 15s:
  - `python main.py --ws-only --ws-backend raw --verify-data`
- Require ticker + candles + heartbeat (may need longer timeout):
  - `python main.py --ws-only --ws-backend raw --verify-data --require-all --verify-timeout 30`
- SDK backend 15s run:
  - `python main.py --ws-only --ws-backend sdk --duration 15`

---

## Strategy Concepts (Reference)

### Dollar-Cost Averaging (DCA)
Buy small amounts of BTC at regular intervals or after defined percentage drops to reduce the impact of volatility and smooth entry price.

### Average True Range (ATR) Stop-Loss
ATR measures market volatility. For active trades, it can set dynamic stop-loss thresholds (e.g., Stop = Entry − k × ATR) that adapt to current conditions and reduce false triggers.
