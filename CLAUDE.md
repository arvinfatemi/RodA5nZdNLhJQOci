# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
```bash
# Run the FastAPI web application (primary interface)
python -m app.main

# Legacy menu system
python scripts/run_app.py

# Install dependencies
pip install -r requirements.txt
```

## Architecture

This is a **BTC Trading Bot 2.0** built with FastAPI featuring Google Sheets configuration, Coinbase WebSocket integration, and Telegram notifications.

### Core Structure
- **`app/main.py`**: FastAPI application entry point with web dashboard
- **`app/config.py`**: Settings management using pydantic-settings
- **`app/api/api_v1/`**: Versioned API endpoints for all services
- **`app/services/`**: Business logic layer containing:
  - `config_service.py`: Google Sheets configuration management
  - `websocket_service.py`: Coinbase WebSocket connections
  - `telegram_service.py`: Telegram bot messaging
  - `bitcoin_service.py`: Bitcoin price and candles data
- **`app/models/`**: Pydantic data models for type safety
- **`app/core/`**: Core utilities and legacy components
- **`app/static/`**: Frontend assets (CSS, JS)
- **`app/templates/`**: Jinja2 HTML templates

### Key Services
1. **ConfigService**: Loads configuration from Google Sheets with caching
2. **WebSocketService**: Manages Coinbase Advanced Trade WebSocket connections
3. **TelegramService**: Handles Telegram bot notifications
4. **BitcoinService**: Fetches Bitcoin price and candle data

### API Endpoints (`/api/v1/`)
- `/config` - Google Sheets configuration management
- `/websocket/*` - Coinbase WebSocket control
- `/telegram/*` - Telegram messaging
- `/bitcoin/*` - Bitcoin price and candle data

### Environment Configuration
Uses `.env` file for configuration. Key variables:
- `GOOGLE_SHEET_ID`: Google Sheets document ID
- `TELEGRAM_BOT_TOKEN`: Telegram bot credentials
- `DEBUG`: Development mode toggle
- `HOST`/`PORT`: Application server settings

### Dependencies
- **FastAPI**: Web framework with automatic API documentation
- **Google Sheets**: `gspread`, `google-auth` for configuration management
- **Coinbase**: `coinbase-advanced-py`, `websocket-client` for trading data
- **Telegram**: Uses stdlib `urllib` for bot messaging
- **Frontend**: Jinja2 templates with static assets

### Development Tools
- `scripts/run_app.py`: Menu-driven interface for individual component testing
- `tools/`: Debugging utilities for Coinbase SDK and WebSocket inspection
- `docs/`: Project documentation (ARCHITECTURE.md, CODE_REVIEW.md, PROJECT_STATUS.md)