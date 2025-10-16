# BTC Trading Bot - Documentation

Complete documentation for setting up, developing, and deploying the BTC Trading Bot.

---

## 🚀 Getting Started

Choose your setup path based on your needs:

### 🎓 [Simple Setup (2 minutes)](SIMPLE_SETUP.md)
**Perfect for**: Students, learning, quick testing, educational use

**What you get**:
- Public Google Sheets integration (no auth required)
- Console-based notifications
- Full trading bot functionality
- Zero external API setup

**Setup time**: ~2 minutes

---

### 🔐 [Advanced Setup](ADVANCED_SETUP.md)
**Perfect for**: Production deployments, private data, advanced features

**What you get**:
- Private Google Sheets with authentication
- External notifications (Telegram, Email)
- Production-ready configuration
- Security best practices

**Setup time**: ~15-30 minutes

---

## 📖 Documentation Index

### Setup & Configuration
- **[Simple Setup](SIMPLE_SETUP.md)** - Quick 2-minute setup for learning
- **[Advanced Setup](ADVANCED_SETUP.md)** - Production setup with authentication

### Development
- **[Architecture](ARCHITECTURE.md)** - Codebase structure and technical overview
- **[Contributing](CONTRIBUTING.md)** - Developer guide and contribution workflow

### Deployment
- **[Production Deployment](DEPLOYMENT.md)** - Deploy to production environments

### Archive
- **[Implementation Notes](archive/)** - Historical implementation documentation

---

## 📋 Quick Links

### For Beginners
1. Start with [Simple Setup](SIMPLE_SETUP.md)
2. Review [Architecture](ARCHITECTURE.md) to understand the codebase
3. Explore the web dashboard at http://localhost:8000

### For Developers
1. Follow [Contributing](CONTRIBUTING.md) guidelines
2. Review [Architecture](ARCHITECTURE.md) for technical details
3. Set up development environment with dev dependencies

### For Production
1. Complete [Advanced Setup](ADVANCED_SETUP.md)
2. Follow [Production Deployment](DEPLOYMENT.md) guide
3. Implement monitoring and backups

---

## 🎯 Common Tasks

### Running the Application
```bash
# Development (simple setup)
python -m app.main

# Production (Docker)
docker-compose up -d
```

### Accessing the Dashboard
- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Configuration
- **Environment**: Edit `.env` file
- **Trading Settings**: Update Google Sheet
- **Credentials**: See [Advanced Setup](ADVANCED_SETUP.md)

---

## 🆘 Getting Help

### Troubleshooting
- **Setup Issues**: Check setup guide for your path
- **Connection Problems**: Review troubleshooting sections
- **Docker Issues**: See [Deployment](DEPLOYMENT.md) guide

### Documentation Issues
If you find issues with documentation:
1. Check if information is outdated
2. Verify steps work on your system
3. Consider contributing improvements

### Contributing
Want to improve the bot? See [Contributing](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- Testing requirements
- Pull request process

---

## 📚 Documentation Structure

```
docs/
├── README.md                 # This file - documentation index
├── SIMPLE_SETUP.md           # Quick 2-minute setup guide
├── ADVANCED_SETUP.md         # Production setup with auth
├── ARCHITECTURE.md           # Technical architecture
├── CONTRIBUTING.md           # Developer guidelines
├── DEPLOYMENT.md             # Production deployment
└── archive/                  # Historical documentation
    ├── simplified-setup-implementation.md
    ├── docker-setup-implementation.md
    ├── weekly-reports-implementation.md
    ├── phase1-code-review.md
    └── project-status-snapshot.md
```

---

## 🔄 Documentation Updates

This documentation is actively maintained. Last updated: 2025-10-16

### Recent Changes
- Split setup guide into Simple and Advanced paths
- Reorganized documentation structure
- Moved implementation notes to archive
- Added comprehensive navigation

### Contributing to Docs
Documentation improvements welcome! See [Contributing](CONTRIBUTING.md).

---

**Ready to get started?** Choose your path:
- 🎓 [Simple Setup (2 min)](SIMPLE_SETUP.md) for learning
- 🔐 [Advanced Setup](ADVANCED_SETUP.md) for production
