# Simple Setup Guide (2 Minutes!)

Perfect for **students, learning, and quick testing** - zero external API setup needed!

## What You'll Need

- **Python 3.10+** (recommended: 3.12)
- **Git** for cloning the repository
- **Google Sheet** (any public sheet with bot configuration)

## What You DON'T Need

- ❌ No Google Cloud account
- ❌ No service accounts or OAuth setup
- ❌ No Telegram bot creation
- ❌ No API keys or credentials

---

## Setup Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd btc-trading-bot
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Configuration

```bash
cp .env.example .env
nano .env  # or use any text editor
```

### 5. Make Your Google Sheet Public

1. Open your Google Sheet with bot configuration
2. Click "Share" button (top right)
3. Change "Restricted" to "Anyone with the link"
4. Set permission to "Viewer"
5. Click "Done"
6. Copy Sheet ID from URL: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`

### 6. Add Sheet ID to .env

```bash
# In .env file, add:
GOOGLE_SHEET_ID=YOUR_SHEET_ID
```

### 7. Run the Bot

```bash
python -m app.main
```

### 8. Access the Dashboard

Open your browser and navigate to:
- **Web Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

**That's it!** Notifications will appear in your console logs.

---

## Docker Option (Alternative)

If you prefer using Docker:

### 1. Clone and Configure

```bash
git clone <repository-url>
cd btc-trading-bot
cp .env.example .env
nano .env  # Add GOOGLE_SHEET_ID only
```

### 2. Run with Docker

```bash
docker-compose -f docker-compose.simple.yml up -d
```

### 3. View Logs

Notifications appear in Docker logs:

```bash
docker-compose -f docker-compose.simple.yml logs -f
```

### 4. Access Dashboard

- **Web Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Stop Application

```bash
docker-compose -f docker-compose.simple.yml down
```

---

## Google Sheet Format

Your Google Sheet should have these columns:

| key | value | type | notes |
|-----|-------|------|-------|
| budget_usd | 10000 | int | Trading budget |
| dca_drop_pct | 3 | float | DCA trigger percentage |
| dca_buy_amount_usd | 500 | float | DCA buy amount |
| data_fetch_interval_min | 30 | int | Data fetch interval |
| enable_dca | true | bool | Enable DCA trading |

**See the full configuration options in the example sheet template.**

---

## How It Works

### Configuration Loading
The bot automatically:
1. Fetches your public Google Sheet as CSV
2. No authentication required
3. Caches configuration locally for performance

### Notifications
By default, all notifications appear in:
- **Console logs** (when running manually)
- **Docker logs** (when running in Docker)

No Telegram or Email setup required!

---

## Troubleshooting

### "Can't access Google Sheet"

**Check**:
- Sheet is set to "Anyone with the link" (public)
- Sheet ID in `.env` is correct
- Internet connection is working

**Solution**:
```bash
# Verify sheet ID format
GOOGLE_SHEET_ID=1A58QwxlFcy2zJGfcPRlBLtlaoC7eundbS6DpG24nMao
```

### "Port 8000 already in use"

**Solution**:
```bash
# Change port in .env
PORT=8080

# Or stop other services using port 8000
```

### Dependencies Installation Fails

**Solution**:
```bash
# Upgrade pip first
pip install --upgrade pip

# Try installing again
pip install -r requirements.txt
```

### Application Won't Start

**Check logs**:
```bash
# View recent errors
tail -f data/logs/app.log

# Or run with debug mode
DEBUG=true python -m app.main
```

---

## Next Steps

Once your bot is running:

1. **Explore the Dashboard**: http://localhost:8000
2. **View API Docs**: http://localhost:8000/docs
3. **Monitor Console**: Watch for notifications and trading decisions
4. **Customize Configuration**: Update your Google Sheet values

### Want More Features?

When you're ready for production deployment:
- **Private Google Sheets** with authentication
- **External Notifications** via Telegram or Email
- **Advanced Security** and credential management

See: [Advanced Setup Guide](ADVANCED_SETUP.md)

---

## What's Running?

The simple setup includes:

- ✅ **Web Dashboard** - Modern UI for monitoring
- ✅ **REST API** - Full API access
- ✅ **Google Sheets Config** - Public sheet integration
- ✅ **Bitcoin Price Data** - Real-time BTC prices
- ✅ **Trading Logic** - DCA decision making
- ✅ **Console Notifications** - All alerts in logs
- ✅ **Data Persistence** - Trade history and state

**All working with zero external API setup!**

---

**Need Help?**

- Check [Architecture](ARCHITECTURE.md) for technical details
- See [Contributing](CONTRIBUTING.md) for development
- Review [Troubleshooting](#troubleshooting) section above
