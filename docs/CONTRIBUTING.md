# Contributing to BTC Trading Bot

Thank you for your interest in contributing to the BTC Trading Bot! This guide will help you get started with development and contributions.

## 🚀 Quick Start

### Development Environment Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/btc-trading-bot.git
   cd btc-trading-bot
   git remote add upstream https://github.com/original/btc-trading-bot.git
   ```

2. **Setup Development Environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # .venv\\Scripts\\activate  # Windows

   # Install all dependencies (including dev dependencies)
   pip install -r requirements.txt
   pip install -r requirements-dev.txt

   # Create data directories
   mkdir -p data/{logs,state,history,cache,backups}

   # Setup environment
   cp .env.example .env
   # Edit .env with your development configuration
   ```

3. **Alternative: Docker Development**
   ```bash
   # Build development environment
   docker-compose -f docker-compose.dev.yml up -d

   # Access development container
   docker-compose -f docker-compose.dev.yml exec app bash
   ```

---

## 📁 Project Structure

Understanding the codebase structure:

```
app/
├── api/api_v1/endpoints/    # API route handlers
├── core/                    # Core business logic
├── models/                  # Pydantic data models
├── services/                # Business service layer
│   ├── config_service.py    # Google Sheets integration
│   ├── websocket_service.py # Coinbase WebSocket
│   ├── telegram_service.py  # Telegram notifications
│   └── bitcoin_service.py   # Bitcoin data fetching
├── static/                  # Frontend assets
├── templates/               # Jinja2 HTML templates
├── config.py               # Application configuration
└── main.py                 # FastAPI application entry
```

### Architecture Principles

- **Service Layer**: Business logic is isolated in services
- **API Layer**: Clean separation between API and business logic
- **Models**: Pydantic models for type safety and validation
- **Configuration**: Environment-based configuration management
- **Testing**: Comprehensive test coverage with mocks for external services

---

## 🛠️ Development Workflow

### Code Style and Quality

We use several tools to maintain code quality:

```bash
# Format code
black app/
black scripts/
black tests/

# Sort imports
isort app/
isort scripts/
isort tests/

# Type checking
mypy app/

# Linting
flake8 app/

# Run all quality checks
./scripts/check-code-quality.sh  # (create this script)
```

### Pre-commit Hooks (Recommended)

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services/test_config_service.py

# Run tests in watch mode (requires pytest-watch)
ptw -- tests/
```

### Development Server

```bash
# Start development server with auto-reload
python -m app.main

# Or use uvicorn directly with reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔄 Contribution Process

### 1. Issue Creation

Before starting work:
- Check existing issues and PRs
- Create an issue for bugs or feature requests
- Discuss approach for major changes

### 2. Branch Naming

Use descriptive branch names:
```bash
# Feature branches
git checkout -b feature/add-coinbase-pro-support
git checkout -b feature/improve-telegram-formatting

# Bug fixes
git checkout -b fix/websocket-connection-error
git checkout -b fix/config-cache-invalidation

# Documentation
git checkout -b docs/update-api-documentation
```

### 3. Commit Messages

Follow conventional commits:
```bash
# Format: type(scope): description

feat(api): add new endpoint for trading history
fix(websocket): handle connection timeout errors
docs(setup): update installation instructions
test(services): add unit tests for telegram service
refactor(config): simplify environment variable handling
```

### 4. Pull Request Process

1. **Update from upstream**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Ensure quality**
   ```bash
   # Run all quality checks
   black app/ scripts/ tests/
   isort app/ scripts/ tests/
   mypy app/
   flake8 app/
   pytest
   ```

3. **Create meaningful PR**
   - Clear title and description
   - Reference related issues
   - Include screenshots for UI changes
   - List testing performed

4. **Review process**
   - Address review feedback
   - Keep PR up to date with main branch
   - Ensure CI passes

---

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_models/         # Model validation tests
│   ├── test_services/       # Service logic tests
│   └── test_utils/          # Utility function tests
├── integration/             # Integration tests
│   ├── test_api/            # API endpoint tests
│   └── test_external/       # External service tests
└── fixtures/                # Test data fixtures
```

### Writing Tests

```python
# Example service test
import pytest
from unittest.mock import Mock, patch
from app.services.telegram_service import TelegramService

class TestTelegramService:
    @pytest.fixture
    def service(self):
        return TelegramService()

    @patch('app.services.telegram_service.urllib.request.urlopen')
    async def test_send_message_success(self, mock_urlopen, service):
        # Setup mock
        mock_response = Mock()
        mock_response.read.return_value = b'{"ok": true}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Test
        result = await service.send_message("Test message")

        # Assert
        assert result is not None
        mock_urlopen.assert_called_once()
```

### Test Coverage

Aim for high test coverage:
- **Models**: 100% - Test all validation logic
- **Services**: 90%+ - Test business logic thoroughly
- **API**: 85%+ - Test endpoints and error handling
- **Utils**: 95%+ - Test utility functions

---

## 🐛 Debugging

### Local Development

```bash
# Enable debug mode
export DEBUG=true

# Detailed logging
export LOG_LEVEL=DEBUG

# Run with debugger
python -m debugpy --listen 5678 --wait-for-client -m app.main
```

### Docker Debugging

```bash
# View logs
docker-compose logs -f btc-trading-bot

# Debug container
docker-compose exec btc-trading-bot python -c "
import app.services.config_service as cs
# Debug here
"

# Interactive shell
docker-compose exec btc-trading-bot bash
```

### Common Issues

1. **Import Errors**
   - Ensure you're in the project root
   - Check Python path: `export PYTHONPATH=.`

2. **API Connection Issues**
   - Verify environment variables
   - Test individual services in isolation

3. **Test Failures**
   - Run tests in isolation: `pytest tests/path/to/test.py::test_function`
   - Check for race conditions in async tests

---

## 📝 Documentation

### Code Documentation

```python
# Service methods should have clear docstrings
class ConfigService:
    async def get_config(self) -> DCAConfig:
        """
        Retrieve configuration from Google Sheets with caching.

        Returns:
            DCAConfig: Validated configuration object

        Raises:
            ConfigurationError: If configuration cannot be loaded
        """
```

### API Documentation

- API endpoints are auto-documented via FastAPI
- Add comprehensive examples in docstrings
- Update OpenAPI descriptions for complex endpoints

### README Updates

When adding features:
- Update feature list in README.md
- Add configuration instructions if needed
- Update API endpoint list

---

## 🔐 Security Guidelines

### Sensitive Data

- Never commit API keys, tokens, or credentials
- Use environment variables for all sensitive configuration
- Add sensitive files to `.gitignore`

### Code Security

```bash
# Security linting
bandit -r app/

# Dependency scanning
safety check

# Secrets scanning
truffleHog --regex --entropy=false .
```

### External Services

- Validate all external API responses
- Implement proper error handling
- Use timeouts for external requests
- Rate limit API calls appropriately

---

## 🚀 Release Process

### Version Management

- Use semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `pyproject.toml`
- Tag releases: `git tag v1.2.3`

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version bumped
- [ ] Docker images built and tested
- [ ] Release notes prepared

---

## 💬 Community Guidelines

### Communication

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and contribute

### Code Reviews

- Review code thoroughly but kindly
- Suggest improvements, don't just point out problems
- Test the changes locally when possible

### Issue Reporting

Use the issue templates:
- **Bug Report**: Provide reproduction steps
- **Feature Request**: Explain use case and benefit
- **Question**: Check documentation first

---

## 📚 Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Telegram Bot API](https://core.telegram.org/bots/api)

### Tools
- [Black](https://black.readthedocs.io/) - Code formatting
- [isort](https://isort.readthedocs.io/) - Import sorting
- [mypy](http://mypy-lang.org/) - Type checking
- [pytest](https://pytest.org/) - Testing framework

---

**Happy Contributing! 🚀**

Thank you for helping make the BTC Trading Bot better for everyone!