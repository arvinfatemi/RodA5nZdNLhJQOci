# BTC Trading Bot - Setup Guide

This guide offers **two setup paths**:
1. **🎓 Simple Path**: Perfect for students and learning (2 minutes)
2. **🔐 Advanced Path**: For production deployments with private data

Choose the path that fits your needs!

---

## 🎓 SIMPLE SETUP (Educational Use - Recommended for Learning)

**Time: 2 minutes | No external API setup required!**

### What You'll Need
- **Python**: 3.10+ (recommended: 3.12)
- **Git**: For cloning the repository
- **Google Sheet**: Any public Google Sheet with bot configuration

### What You DON'T Need
- ❌ No Google Cloud account
- ❌ No service accounts or OAuth setup
- ❌ No Telegram bot creation
- ❌ No API keys or credentials

### Step-by-Step Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd btc-trading-bot
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup configuration:**
   ```bash
   cp .env.example .env
   nano .env  # or any text editor
   ```

5. **Make your Google Sheet public:**
   - Open your Google Sheet with bot configuration
   - Click "Share" button (top right)
   - Change "Restricted" to "Anyone with the link"
   - Set permission to "Viewer"
   - Click "Done"
   - Copy Sheet ID from URL: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`

6. **Add Sheet ID to .env:**
   ```bash
   GOOGLE_SHEET_ID=YOUR_SHEET_ID
   ```

7. **Run the bot:**
   ```bash
   python -m app.main
   ```

8. **Access the dashboard:**
   - Open http://localhost:8000 in your browser
   - Notifications will appear in console logs

**That's it! You're done.** The bot will:
- Fetch config from your public sheet (no auth needed)
- Log notifications to console (no Telegram/Email setup needed)
- Work immediately without any external API setup

### Docker Simple Setup (Alternative)

If you prefer Docker for the simple setup:

1. **Clone and configure:**
   ```bash
   git clone <repository-url>
   cd btc-trading-bot
   cp .env.example .env
   nano .env  # Add GOOGLE_SHEET_ID only
   ```

2. **Run with Docker:**
   ```bash
   docker-compose -f docker-compose.simple.yml up -d
   ```

3. **View logs (notifications appear here):**
   ```bash
   docker-compose -f docker-compose.simple.yml logs -f
   ```

4. **Access dashboard:**
   - Open http://localhost:8000

**Total time with Docker: ~2 minutes**

---

## 🔐 ADVANCED SETUP (Production Use - Private Sheets & External Notifications)

**For deployments requiring private sheets and external notifications**

### System Requirements
- **Python**: 3.10+ (recommended: 3.12)
- **Docker**: 20.10+ with Docker Compose (optional but recommended)
- **Git**: For cloning the repository
- **Internet Connection**: For API access to Google Sheets, Coinbase, and external services

### Required Accounts & API Access
1. **Google Account**: For Google Sheets integration (with Cloud Console access)
2. **Telegram OR Email Account**: For external notifications (optional)
3. **Coinbase Account**: (Optional) For enhanced trading data

---

## 🐳 Docker Setup (Recommended for Advanced/Production)

### Prerequisites
- Docker 20.10+ installed
- Docker Compose installed
- Credential files ready (if using private sheets)

### Setup Steps

1. **Clone repository and prepare environment:**
   ```bash
   git clone <repository-url>
   cd btc-trading-bot
   cp .env.example .env
   ```

2. **Configure environment:**
   ```bash
   nano .env  # Add all credentials (see Configuration section below)
   ```

3. **Add credential files (if using private sheets):**
   ```bash
   # For service account auth:
   cp /path/to/your-credentials.json service_account.json

   # For Telegram or Email, configure in .env (no files needed)
   ```

4. **Edit docker-compose.yml:**
   - Open `docker-compose.yml`
   - Uncomment the volume mounts for credential files:
     ```yaml
     # Uncomment these lines:
     - ./service_account.json:/app/service_account.json:ro
     # or
     - ./token.json:/app/data/cache/token.json
     ```

5. **Start application:**
   ```bash
   docker-compose up -d
   ```

6. **Access application:**
   - Web: http://localhost:8000
   - API: http://localhost:8000/docs

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

### Troubleshooting Docker

**Error: "No such file or directory: service_account.json"**
- Comment out the volume mount in `docker-compose.yml` if not using service account
- Or create an empty file: `touch service_account.json`

**Notifications not showing:**
- Check logs: `docker-compose logs -f`
- Console notifications appear in Docker logs by default

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

#### Option 1: Public Sheet (Simplest - No Auth Required!)
1. **Make your sheet public**:
   - Open your Google Sheet
   - Click "Share" button (top right)
   - Change "Restricted" to "Anyone with the link"
   - Set permission to "Viewer"
   - Click "Done"

2. **Get Sheet ID**:
   - Copy from URL: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`

3. **Configure Environment**:
   ```bash
   # In .env file
   GOOGLE_SHEET_ID=your_sheet_id_here
   GOOGLE_WORKSHEET_NAME=Sheet1
   # That's it! No other credentials needed
   ```

**Note**: The bot will automatically fetch the sheet as CSV without any authentication. Perfect for educational use or non-sensitive data.

#### Option 2: Service Account (For Private Sheets)
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

#### Option 3: OAuth (Alternative for Private Sheets)
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

### Notification Setup (Pick One or None)

The bot uses a **smart fallback chain** for notifications:
1. Telegram (if configured)
2. Email (if configured)
3. Console logs (always available)

#### Option 1: Console Logs (Default - No Setup Required)
Just leave both Telegram and Email empty in `.env`. Notifications will automatically log to console.

**Best for**: Learning, development, and educational use.

#### Option 2: Email Notifications (Simple SMTP Setup)

1. **Get Email Credentials**:
   - **Gmail**: Generate app password at [Google Account Security](https://myaccount.google.com/apppasswords)
   - **Outlook**: Use your regular password or app password
   - **Other SMTP**: Get credentials from your email provider

2. **Configure Environment**:
   ```bash
   # In .env file
   EMAIL_SMTP_HOST=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_FROM=your-bot@gmail.com
   EMAIL_PASSWORD=your_app_password_here
   EMAIL_TO=notifications@example.com
   ```

**Best for**: Production deployments, personal projects, scheduled reports.

#### Option 3: Telegram Bot (Most Feature-Rich)

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

**Best for**: Mobile alerts, real-time notifications, advanced integrations.

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