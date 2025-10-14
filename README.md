# BTC Trading Bot 2.0

A modern, professional BTC Trading Bot built with FastAPI, featuring Google Sheets configuration, Coinbase WebSocket integration, Telegram notifications, and real-time Bitcoin price data.

## 🚀 Features

- **Web Dashboard**: Modern web interface with real-time updates
- **Smart Configuration Loading**: Google Sheets with automatic fallback (public CSV → no auth needed!)
- **Flexible Notifications**: Telegram, Email, or Console logs with automatic fallback chain
- **Coinbase WebSocket**: Real-time BTC price data and candles
- **Bitcoin API**: Fetch current prices and historical candle data
- **Educational First**: Zero external API setup required - perfect for learning
- **Professional Architecture**: Modular, scalable, and production-ready when needed

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
├── data/                       # Data storage (ignored by git)
│   ├── logs/                   # Application logs
│   ├── state/                  # Runtime state files
│   ├── history/                # Trading history
│   ├── cache/                  # Cache files
│   └── backups/                # Configuration backups
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md         # Architecture overview
│   ├── SETUP.md                # Detailed setup guide
│   ├── CONTRIBUTING.md         # Development guide
│   └── DEPLOYMENT.md           # Production deployment
├── scripts/                    # Utility scripts
├── tools/                      # Debug utilities
├── tests/                      # Test modules
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose setup
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
└── pyproject.toml             # Modern Python project configuration
```

## 🚀 Quick Start (2 Minutes!)

Perfect for students and educational use - zero external API setup needed!

### Simple Setup (Recommended for Learning)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd btc-trading-bot
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Setup configuration:**
   ```bash
   cp .env.example .env
   nano .env  # Just add your Google Sheet ID (see below)
   ```

4. **Make your Google Sheet public:**
   - Open your Google Sheet with bot configuration
   - Click "Share" button (top right)
   - Change "Restricted" to "Anyone with the link"
   - Set permission to "Viewer"
   - Copy the Sheet ID from URL: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`
   - Paste it in `.env` as `GOOGLE_SHEET_ID=YOUR_SHEET_ID`

5. **Run the bot:**
   ```bash
   python -m app.main
   ```

6. **Access the application:**
   - Web Dashboard: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

**That's it!** No Google OAuth, no Telegram bot creation, no credentials needed.
Notifications will appear in your console logs.

---

## 🐳 Docker Setup (Alternative)

### Simple Docker Setup (Recommended for Students)

Perfect for learning - no credential files needed!

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd btc-trading-bot
   cp .env.example .env
   # Edit .env: Just add GOOGLE_SHEET_ID (public sheet)
   ```

2. **Run with simple compose file:**
   ```bash
   docker-compose -f docker-compose.simple.yml up -d
   ```

3. **View logs (notifications appear here):**
   ```bash
   docker-compose -f docker-compose.simple.yml logs -f
   ```

4. **Access the application:**
   - Web Dashboard: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Advanced Docker Setup (For Production)

With credential files for private sheets and external notifications:

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd btc-trading-bot
   cp .env.example .env
   # Edit .env with all credentials
   ```

2. **Add credential files (optional):**
   ```bash
   # If using private sheets with service account:
   cp your-credentials.json service_account.json

   # If using Telegram or Email, configure in .env
   ```

3. **Uncomment volume mounts in docker-compose.yml:**
   - Edit `docker-compose.yml`
   - Uncomment the service_account.json or token.json lines if needed

4. **Run with full compose file:**
   ```bash
   docker-compose up -d
   ```

5. **Access the application:**
   - Web Dashboard: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### 🐍 Manual Installation

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

5. **Create data directories:**
   ```bash
   mkdir -p data/{logs,state,history,cache,backups}
   ```

## 🚀 Running the Application

### 🐳 Docker (Recommended)

**Simple setup:**
```bash
# Start in background
docker-compose -f docker-compose.simple.yml up -d

# View logs (shows notifications)
docker-compose -f docker-compose.simple.yml logs -f

# Stop application
docker-compose -f docker-compose.simple.yml down
```

**Advanced setup (with credentials):**
```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop application
docker-compose down
```

### 🐍 Manual Execution
```bash
# Web Application (Recommended)
python -m app.main

# Legacy Menu System
python scripts/run_app.py
```

### 🔗 Application URLs
- **Web Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📖 API Documentation

Once the application is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## ⚙️ Configuration

The application uses environment variables for configuration with **smart fallbacks** for ease of use.

### Required Configuration
- **Google Sheets**: Just the Sheet ID! (No authentication needed if sheet is public)

### Optional Configuration
- **Notifications**: Choose Telegram, Email, or Console logs (default)
- **Google Auth**: Service account or OAuth (only if you want private sheets)
- **Coinbase**: API keys for enhanced features
- **Application**: Debug mode, host, port settings

### Configuration Flexibility

#### Google Sheets (Pick One)
1. **Simple (Educational)**: Make sheet public → Zero setup!
2. **Advanced (Production)**: Use service account or OAuth for private sheets

#### Notifications (Pick One or None)
1. **Console Logs**: Default, no setup required (perfect for learning)
2. **Email**: Standard SMTP (Gmail app passwords work great)
3. **Telegram**: Create bot via @BotFather (most feature-rich)

### Configuration Files
- `.env` - Your local environment variables (copy from `.env.example`)
- `service_account.json` - Optional: Google Service Account credentials
- `token.json` - Optional: OAuth token (auto-generated)

For detailed setup instructions, see [docs/SETUP.md](docs/SETUP.md).

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