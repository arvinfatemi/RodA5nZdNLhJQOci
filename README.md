# BTC Trading Bot 2.0

A modern, professional BTC Trading Bot built with FastAPI, featuring Google Sheets configuration, Coinbase WebSocket integration, Telegram notifications, and real-time Bitcoin price data.

## 🚀 Features

- **Web Dashboard**: Modern web interface with real-time updates
- **Google Sheets Integration**: Load configuration from Google Sheets
- **Coinbase WebSocket**: Real-time BTC price data and candles
- **Telegram Bot**: Send notifications via Telegram
- **Bitcoin API**: Fetch current prices and historical candle data
- **Professional Architecture**: Modular, scalable, and maintainable code structure

## 📁 Project Structure

```
btc_trading_bot/
├── app/                        # Main application package
│   ├── api/api_v1/             # API version 1
│   │   └── endpoints/          # API endpoint modules
│   ├── core/                   # Core business logic modules
│   ├── models/                 # Pydantic models
│   ├── services/               # Service layer
│   ├── static/                 # Static files (CSS, JS, images)
│   ├── templates/              # Jinja2 HTML templates
│   ├── config.py               # Configuration management
│   └── main.py                 # FastAPI application
├── scripts/                    # Utility scripts
├── tests/                      # Test modules
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
└── pyproject.toml             # Modern Python project configuration
```

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd btc-trading-bot
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## 🚀 Running the Application

### Web Application (Recommended)
```bash
python -m app.main
```
Then visit: http://localhost:8000

### Legacy Menu System
```bash
python scripts/run_app.py
```

## 📖 API Documentation

Once the application is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## ⚙️ Configuration

The application uses environment variables for configuration. See `.env.example` for all available options:

- **Google Sheets**: Configure sheet ID and credentials
- **Telegram Bot**: Set bot token and chat ID
- **Coinbase**: Optional API keys for enhanced features
- **Application**: Debug mode, host, port settings

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_refactored_app.py
```

For development with testing tools:
```bash
pip install -r requirements-dev.txt
pytest
```

## 🏗️ Architecture

### Key Improvements in 2.0

- **Modular Design**: Separated concerns with clear boundaries
- **Service Layer**: Business logic isolated from API layer
- **Pydantic Models**: Type-safe request/response validation
- **Template Engine**: Jinja2 templates for maintainable HTML
- **Static Assets**: Proper CSS/JS organization
- **Configuration Management**: Environment-based settings
- **API Versioning**: Future-proof API design
- **Professional Structure**: Industry-standard project layout

### Service Layer

- `ConfigService`: Google Sheets configuration management
- `WebSocketService`: Coinbase WebSocket connections
- `TelegramService`: Telegram bot messaging
- `BitcoinService`: Bitcoin price and candles data

## 🔧 Development

### Code Quality Tools

```bash
# Format code
black app/

# Sort imports  
isort app/

# Type checking
mypy app/

# Linting
flake8 app/
```

### Adding New Features

1. Create models in `app/models/`
2. Implement business logic in `app/services/`
3. Add API endpoints in `app/api/api_v1/endpoints/`
4. Update templates and static files as needed

## 📝 API Endpoints

### v1 API (`/api/v1/`)

- `GET /config` - Fetch Google Sheets configuration
- `POST /websocket/start` - Start Coinbase WebSocket
- `POST /websocket/stop` - Stop Coinbase WebSocket  
- `GET /websocket/status` - Get WebSocket status
- `POST /telegram/send` - Send Telegram message
- `GET /bitcoin/price` - Get current Bitcoin price
- `GET /bitcoin/candles` - Get Bitcoin candle data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Links

- **Documentation**: Available at `/docs` when running
- **Health Check**: `/health` endpoint
- **Static Assets**: `/static/` for CSS, JS, images

---

**BTC Trading Bot 2.0** - Professional trading bot with modern web architecture.