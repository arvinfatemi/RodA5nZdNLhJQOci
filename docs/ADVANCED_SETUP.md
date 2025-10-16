# Advanced Setup Guide

For **production deployments** with private Google Sheets and external notifications.

## Prerequisites

- **Python 3.10+** (recommended: 3.12)
- **Docker 20.10+** with Docker Compose (recommended)
- **Google Cloud account** for private sheets
- **Internet connection** for API access

---

## System Requirements

### Minimum Specifications
- **RAM**: 512 MB
- **CPU**: 1 core
- **Storage**: 1 GB
- **Network**: Stable internet connection

### Recommended for Production
- **RAM**: 1-2 GB
- **CPU**: 2 cores
- **Storage**: 5 GB (with logs)
- **Network**: High availability

---

## Quick Start with Docker (Recommended)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd btc-trading-bot
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your production credentials:

```bash
# Google Sheets
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_WORKSHEET_NAME=Sheet1
GOOGLE_APPLICATION_CREDENTIALS=./service_account.json

# Notifications (choose one or both)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=btc-bot@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=alerts@example.com

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

### 3. Add Credential Files

```bash
# For private Google Sheets
cp /path/to/your-service-account-key.json service_account.json
```

### 4. Edit docker-compose.yml

Uncomment the credential file volume mounts:

```yaml
volumes:
  - ./service_account.json:/app/service_account.json:ro  # Uncomment this
```

### 5. Start Application

```bash
docker-compose up -d
```

### 6. Verify Deployment

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Test health endpoint
curl http://localhost:8000/health
```

---

## Manual Installation

### 1. Setup Python Environment

```bash
# Clone repository
git clone <repository-url>
cd btc-trading-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir -p data/{logs,state,history,cache,backups}

# Setup environment
cp .env.example .env
```

### 2. Configure Services

Edit `.env` with all required credentials (see Configuration section below).

### 3. Run Application

```bash
# Start web application
python -m app.main

# Access dashboard
# http://localhost:8000
```

---

## Configuration

### Google Sheets Authentication

Choose one authentication method:

#### Option 1: Service Account (Recommended)

**Step 1**: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing one
3. Note the project ID

**Step 2**: Enable Google Sheets API
1. Navigate to "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click "Enable"

**Step 3**: Create Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in details:
   - Name: `btc-trading-bot`
   - Description: `Service account for BTC trading bot`
4. Click "Create and Continue"
5. Skip optional steps, click "Done"

**Step 4**: Create and Download Key
1. Find your new service account in the list
2. Click on it to open details
3. Go to "Keys" tab
4. Click "Add Key" → "Create new key"
5. Choose "JSON" format
6. Click "Create" - file downloads automatically

**Step 5**: Setup Credentials
```bash
# Rename downloaded file
mv ~/Downloads/project-name-*.json service_account.json
```

**Step 6**: Share Google Sheet
1. Open your Google Sheet
2. Click "Share" button
3. Add the service account email (found in JSON file as `client_email`)
   - Example: `btc-trading-bot@project-id.iam.gserviceaccount.com`
4. Grant "Editor" permissions
5. Click "Send"

**Step 7**: Configure Environment
```bash
# In .env file
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_APPLICATION_CREDENTIALS=./service_account.json
```

#### Option 2: OAuth 2.0

**Step 1**: Create OAuth Credentials
1. In Google Cloud Console → "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Desktop Application"
4. Name it: `btc-trading-bot-oauth`
5. Click "Create"
6. Download JSON file

**Step 2**: Configure Environment
```bash
# Rename downloaded file
mv ~/Downloads/client_secret_*.json credentials.json

# In .env file
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_OAUTH_CLIENT_SECRETS=./credentials.json
GOOGLE_OAUTH_TOKEN_PATH=./data/cache/token.json
```

**Step 3**: First Run Authentication
```bash
# Run the bot - browser will open for OAuth consent
python -m app.main

# Follow browser prompts to authorize
# Token saved to data/cache/token.json
```

---

### Telegram Notifications

**Step 1**: Create Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow prompts:
   - Bot name: `BTC Trading Bot` (or your choice)
   - Bot username: `your_btc_bot` (must end with `bot`)
4. Save the bot token provided

**Step 2**: Get Chat ID

**Method A** - Personal messages:
```bash
# Send a message to your bot in Telegram first
# Then visit this URL in browser (replace TOKEN):
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates

# Look for "chat":{"id":123456789
# That number is your chat ID
```

**Method B** - Using helper script:
```bash
# After sending a message to your bot
python -c "
from app.core.telegram_notifier import resolve_and_cache_chat_id
resolve_and_cache_chat_id(env_path='.env')
"
```

**Step 3**: Configure Environment
```bash
# In .env file
TELEGRAM_BOT_TOKEN=123456:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Or use username for channels
TELEGRAM_CHAT_USERNAME=@your_channel
```

---

### Email Notifications

#### Gmail Setup

**Step 1**: Create App Password
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication (if not enabled)
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Select app: "Mail"
5. Select device: "Other" → "BTC Trading Bot"
6. Click "Generate"
7. Save the 16-character password

**Step 2**: Configure Environment
```bash
# In .env file
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_TO=recipient@example.com
```

#### Other Email Providers

**Outlook/Office365**:
```bash
EMAIL_SMTP_HOST=smtp-mail.outlook.com
EMAIL_SMTP_PORT=587
```

**Yahoo**:
```bash
EMAIL_SMTP_HOST=smtp.mail.yahoo.com
EMAIL_SMTP_PORT=587
```

**Custom SMTP**:
```bash
EMAIL_SMTP_HOST=mail.yourdomain.com
EMAIL_SMTP_PORT=587  # or 465 for SSL
```

---

## Docker Production Deployment

### Production docker-compose.yml

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  btc-trading-bot:
    build: .
    container_name: btc-trading-bot-prod
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./service_account.json:/app/service_account.json:ro
      - /etc/localtime:/etc/localtime:ro
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

### Start Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## Security Best Practices

### Environment Variables
- Never commit `.env` files to git
- Use secrets management in production
- Rotate credentials regularly
- Use minimum required permissions

### Network Security
- Use reverse proxy (Nginx/Traefik) with SSL
- Enable firewall rules
- Restrict port access
- Use VPN for remote access

### Google Sheets
- Use service accounts with minimal permissions
- Share sheets with specific service account only
- Regular audit of shared users
- Enable sheet version history

### Credentials Storage
```bash
# Secure file permissions
chmod 600 .env
chmod 600 service_account.json

# Never share these files
# Add to .gitignore (already included)
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Docker health
docker inspect --format='{{.State.Health.Status}}' btc-trading-bot-prod
```

### Logs

```bash
# View application logs
tail -f data/logs/app.log

# Docker logs
docker-compose logs -f

# Error logs only
docker-compose logs --tail=100 | grep ERROR
```

### Backups

```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Backup configuration
cp .env .env.backup
cp service_account.json service_account.json.backup
```

---

## Troubleshooting

### Google Sheets Access Denied

**Check**:
- Service account email is shared on sheet
- Sheet ID is correct in `.env`
- Service account JSON file is valid
- Google Sheets API is enabled

**Solution**:
```bash
# Verify credentials
cat service_account.json | grep client_email

# Test API access
python -c "
from app.services.config_service import ConfigService
import asyncio
async def test():
    service = ConfigService()
    config = await service.get_config()
    print('Success!')
asyncio.run(test())
"
```

### Telegram Not Working

**Check**:
- Bot token is correct
- Chat ID is correct
- Bot has been started by user
- No webhook configured for bot

**Solution**:
```bash
# Test telegram
curl https://api.telegram.org/botYOUR_TOKEN/getMe

# Send test message
python -c "
from app.services.telegram_service import TelegramService
import asyncio
async def test():
    service = TelegramService()
    await service.send_message('Test message')
asyncio.run(test())
"
```

### Email Sending Fails

**Check**:
- SMTP credentials are correct
- App password is used (not regular password)
- SMTP port is correct (587 for TLS, 465 for SSL)
- Firewall allows outbound SMTP

**Solution**:
```bash
# Test SMTP connection
python -c "
import smtplib
from app.config import Settings
settings = Settings()
server = smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port)
server.starttls()
server.login(settings.email_from, settings.email_password)
print('SMTP connection successful!')
server.quit()
"
```

### Docker Container Won't Start

**Check logs**:
```bash
docker-compose logs btc-trading-bot
```

**Common issues**:
- Credential file not mounted correctly
- Port 8000 already in use
- Invalid environment variables

---

## Performance Tuning

### Resource Limits

```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Application Settings

```bash
# In .env - adjust based on your needs
DATA_FETCH_INTERVAL_MIN=30  # Lower = more frequent checks
MAX_CONNECTIONS=20          # API connection pool
CACHE_TTL=300              # Cache time-to-live in seconds
```

---

## Next Steps

1. **Test Configuration**: Verify all services work
2. **Monitor Performance**: Watch logs and metrics
3. **Setup Backups**: Automated backup schedule
4. **Enable Monitoring**: Add Prometheus/Grafana
5. **Production Hardening**: See [Deployment Guide](DEPLOYMENT.md)

---

**For production deployment details, see**: [DEPLOYMENT.md](DEPLOYMENT.md)

**For development and contributions, see**: [CONTRIBUTING.md](CONTRIBUTING.md)
