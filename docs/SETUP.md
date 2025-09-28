# BTC Trading Bot - Setup Guide

This comprehensive guide will help you set up the BTC Trading Bot from scratch.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.10+ (recommended: 3.12)
- **Docker**: 20.10+ with Docker Compose (optional but recommended)
- **Git**: For cloning the repository
- **Internet Connection**: For API access to Google Sheets, Coinbase, and Telegram

### Required Accounts & API Access
1. **Google Account**: For Google Sheets integration
2. **Telegram Account**: For bot notifications
3. **Coinbase Account**: (Optional) For enhanced trading data

---

## 🐳 Docker Setup (Recommended)

### Quick Start
```bash
# 1. Clone repository
git clone <repository-url>
cd btc-trading-bot

# 2. Setup environment
cp .env.example .env

# 3. Configure (see Configuration section below)
nano .env  # or your preferred editor

# 4. Start application
docker-compose up -d

# 5. Access application
# Web: http://localhost:8000
# API: http://localhost:8000/docs
```

### Docker Management Commands
```bash
# View logs
docker-compose logs -f

# Restart application
docker-compose restart

# Stop application
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Access container shell
docker-compose exec btc-trading-bot bash
```

---

## 🐍 Manual Setup

### 1. Clone and Prepare Environment
```bash
# Clone repository
git clone <repository-url>
cd btc-trading-bot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# .venv\\Scripts\\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir -p data/{logs,state,history,cache,backups}

# Setup environment file
cp .env.example .env
```

### 2. Configure Environment Variables
Edit `.env` file with your settings (see Configuration section below).

### 3. Run Application
```bash
# Start web application
python -m app.main

# Or use legacy menu system
python scripts/run_app.py
```

---

## ⚙️ Configuration

### Google Sheets Setup

#### Option 1: Service Account (Recommended)
1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing one

2. **Enable Google Sheets API**:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google Sheets API" and enable it

3. **Create Service Account**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Fill in details and create
   - Download JSON key file

4. **Setup Credentials**:
   ```bash
   # Place the downloaded JSON file as service_account.json
   cp /path/to/downloaded-credentials.json service_account.json
   ```

5. **Share Google Sheet**:
   - Open your Google Sheet
   - Share with service account email (found in service_account.json)
   - Grant "Editor" permissions

6. **Configure Environment**:
   ```bash
   # In .env file
   GOOGLE_SHEET_ID=your_sheet_id_here
   GOOGLE_WORKSHEET_NAME=Sheet1
   GOOGLE_APPLICATION_CREDENTIALS=./service_account.json
   ```

#### Option 2: OAuth (Alternative)
1. **Create OAuth Credentials**:
   - In Google Cloud Console → "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop Application"
   - Download JSON file

2. **Configure Environment**:
   ```bash
   # In .env file
   GOOGLE_SHEET_ID=your_sheet_id_here
   GOOGLE_OAUTH_CLIENT_SECRETS=./client_secrets.json
   GOOGLE_OAUTH_TOKEN_PATH=./data/cache/token.json
   ```

### Telegram Bot Setup

1. **Create Telegram Bot**:
   - Message @BotFather on Telegram
   - Send `/newbot` command
   - Follow instructions to create bot
   - Save the bot token

2. **Get Chat ID**:
   ```bash
   # Method 1: Send message to bot, then visit:
   # https://api.telegram.org/bot<BOT_TOKEN>/getUpdates

   # Method 2: Use @userinfobot to get your user ID
   ```

3. **Configure Environment**:
   ```bash
   # In .env file
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   # OR
   TELEGRAM_CHAT_USERNAME=@your_username
   ```

### Coinbase Setup (Optional)

1. **Create Coinbase Account**:
   - Sign up at [Coinbase](https://www.coinbase.com/)

2. **Generate API Keys** (Optional):
   - Go to Settings → API
   - Create new API key
   - Save credentials securely

3. **Configure Environment**:
   ```bash
   # In .env file (optional)
   COINBASE_API_KEY=your_api_key
   COINBASE_API_SECRET=your_api_secret
   COINBASE_CANDLES_GRANULARITY=30m
   ```

---

## 🧪 Validation & Testing

### Environment Validation
```bash
# Check Python version
python --version

# Check dependencies
pip list

# Test configuration
python -c "from app.config import Settings; print('Config loaded successfully')"
```

### API Connectivity Tests
```bash
# Test Google Sheets connection
python -c "
from app.services.config_service import ConfigService
import asyncio
async def test():
    service = ConfigService()
    config = await service.get_config()
    print('Google Sheets: ✓')
asyncio.run(test())
"

# Test Telegram bot
python -c "
from app.services.telegram_service import TelegramService
import asyncio
async def test():
    service = TelegramService()
    await service.send_message('Setup test successful! 🚀')
asyncio.run(test())
"
```

### Application Health Check
```bash
# After starting the application
curl http://localhost:8000/health

# Expected response: {"status": "healthy"}
```

---

## 🔧 Troubleshooting

### Common Issues

#### Google Sheets Access
**Error**: "Permission denied" or "Forbidden"
- **Solution**: Ensure service account email has access to the sheet
- **Check**: Verify GOOGLE_SHEET_ID is correct (extract from sheet URL)

#### Telegram Bot Not Working
**Error**: "Bot token invalid"
- **Solution**: Verify TELEGRAM_BOT_TOKEN is correct
- **Check**: Ensure bot is not used by another instance

#### Port Already in Use
**Error**: "Port 8000 is already in use"
- **Solution**: Change PORT in .env or stop other services
- **Alternative**: Use `docker-compose down` to stop existing containers

#### Docker Issues
**Error**: "Cannot connect to Docker daemon"
- **Solution**: Ensure Docker is running
- **Check**: Run `docker --version` and `docker-compose --version`

### Logs and Debugging

#### Docker Logs
```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs btc-trading-bot
```

#### Manual Logs
```bash
# Application logs location
ls -la data/logs/

# View recent logs
tail -f data/logs/app.log
```

#### Debug Mode
```bash
# Enable debug mode in .env
DEBUG=true

# Restart application to apply changes
```

---

## 📊 Google Sheet Format

### Required Sheet Structure
Your Google Sheet should have the following columns:

| key | value | type | notes |
|-----|-------|------|-------|
| budget_usd | 10000 | int | Trading budget |
| dca_drop_pct | 3 | float | DCA trigger percentage |
| dca_buy_amount_usd | 500 | float | DCA buy amount |
| atr_period | 14 | int | ATR calculation period |
| atr_multiplier | 1.5 | float | ATR multiplier |
| mode | hybrid | enum | dca/swing/hybrid |
| data_fetch_interval_min | 30 | int | Data fetch interval |
| enable_dca | true | bool | Enable DCA trading |

### Example Sheet Setup
1. Create new Google Sheet
2. Add headers in row 1: `key`, `value`, `type`, `notes`
3. Add your configuration rows below
4. Share with service account email

---

## 🚀 Production Deployment

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).

---

## 🤝 Need Help?

- **Issues**: Check [CONTRIBUTING.md](CONTRIBUTING.md) for bug reports
- **Features**: See project documentation in `docs/`
- **Architecture**: Review [ARCHITECTURE.md](ARCHITECTURE.md)

---

**Next Steps**: Once setup is complete, visit http://localhost:8000 to access the web dashboard!