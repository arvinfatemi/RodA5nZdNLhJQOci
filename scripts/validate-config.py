#!/usr/bin/env python3
"""
BTC Trading Bot - Configuration Validation Script

This script validates all configuration aspects of the BTC Trading Bot,
including environment variables, credentials, and external API connectivity.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import urllib.request
import urllib.parse
import ssl

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ConfigValidator:
    """Configuration validation utility."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def error(self, message: str):
        """Add an error message."""
        self.issues.append(f"ERROR: {message}")
        print(f"❌ {message}")

    def warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(f"WARNING: {message}")
        print(f"⚠️  {message}")

    def success(self, message: str):
        """Print a success message."""
        print(f"✅ {message}")

    def info(self, message: str):
        """Print an info message."""
        print(f"ℹ️  {message}")

    def load_env_file(self) -> Dict[str, str]:
        """Load environment variables from .env file."""
        env_file = self.project_root / '.env'
        env_vars = {}

        if not env_file.exists():
            self.error(".env file not found. Copy .env.example to .env and configure it.")
            return {}

        try:
            with open(env_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    if '=' not in line:
                        self.warning(f"Invalid format in .env line {line_num}: {line}")
                        continue

                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')  # Remove quotes

                    if value:  # Only add non-empty values
                        env_vars[key] = value

            self.success(f"Loaded {len(env_vars)} environment variables from .env")
            return env_vars

        except Exception as e:
            self.error(f"Failed to read .env file: {e}")
            return {}

    def validate_required_config(self, env_vars: Dict[str, str]) -> bool:
        """Validate required configuration variables."""
        print("\n📋 Validating Required Configuration...")

        required_vars = {
            'GOOGLE_SHEET_ID': 'Google Sheets document ID',
            'TELEGRAM_BOT_TOKEN': 'Telegram bot token'
        }

        all_present = True
        for var, description in required_vars.items():
            if var not in env_vars or not env_vars[var]:
                self.error(f"Missing required variable: {var} ({description})")
                all_present = False
            else:
                self.success(f"{var}: ****{env_vars[var][-4:]} (configured)")

        return all_present

    def validate_optional_config(self, env_vars: Dict[str, str]):
        """Validate optional configuration variables."""
        print("\n⚙️ Validating Optional Configuration...")

        optional_vars = {
            'GOOGLE_WORKSHEET_NAME': 'Sheet1',
            'TELEGRAM_CHAT_ID': 'Auto-detected if not set',
            'TELEGRAM_CHAT_USERNAME': 'Alternative to CHAT_ID',
            'DEBUG': 'false',
            'HOST': '0.0.0.0',
            'PORT': '8000',
            'COINBASE_CANDLES_GRANULARITY': '30m'
        }

        for var, default in optional_vars.items():
            if var in env_vars:
                self.info(f"{var}: {env_vars[var]}")
            else:
                self.info(f"{var}: using default ({default})")

    def validate_google_credentials(self) -> bool:
        """Validate Google API credentials."""
        print("\n🔑 Validating Google Credentials...")

        service_account = self.project_root / 'service_account.json'
        token_file = self.project_root / 'token.json'

        if service_account.exists():
            try:
                with open(service_account, 'r') as f:
                    creds = json.load(f)

                required_fields = [
                    'type', 'project_id', 'private_key_id', 'private_key',
                    'client_email', 'client_id', 'auth_uri', 'token_uri'
                ]

                missing_fields = [field for field in required_fields if field not in creds]
                if missing_fields:
                    self.error(f"service_account.json missing fields: {missing_fields}")
                    return False

                if creds.get('type') != 'service_account':
                    self.error("service_account.json type should be 'service_account'")
                    return False

                self.success("service_account.json format is valid")
                self.info(f"Service account email: {creds.get('client_email')}")
                return True

            except json.JSONDecodeError:
                self.error("service_account.json is not valid JSON")
                return False
            except Exception as e:
                self.error(f"Error reading service_account.json: {e}")
                return False

        elif token_file.exists():
            self.info("Using OAuth token.json (service_account.json not found)")
            return True
        else:
            self.error("Neither service_account.json nor token.json found")
            self.info("For service account: Place your Google Cloud service account JSON file as 'service_account.json'")
            self.info("For OAuth: The token.json file will be created during first authentication")
            return False

    async def test_google_sheets_api(self, env_vars: Dict[str, str]) -> bool:
        """Test Google Sheets API connectivity."""
        print("\n📊 Testing Google Sheets API...")

        if 'GOOGLE_SHEET_ID' not in env_vars:
            self.error("Cannot test Google Sheets API: GOOGLE_SHEET_ID not configured")
            return False

        try:
            # Set environment variables
            for key, value in env_vars.items():
                os.environ[key] = value

            from app.services.config_service import ConfigService

            config_service = ConfigService()
            config = await config_service.get_config()

            if config:
                self.success("Google Sheets API connection successful")
                self.info(f"Loaded configuration with {len(config.dict())} settings")
                return True
            else:
                self.error("Google Sheets API returned empty configuration")
                return False

        except ImportError as e:
            self.error(f"Import error: {e}")
            self.info("Make sure all dependencies are installed: pip install -r requirements.txt")
            return False
        except Exception as e:
            self.error(f"Google Sheets API test failed: {e}")
            self.info("Check your GOOGLE_SHEET_ID and ensure the service account has access to the sheet")
            return False

    def test_telegram_bot_api(self, env_vars: Dict[str, str]) -> bool:
        """Test Telegram Bot API connectivity."""
        print("\n📱 Testing Telegram Bot API...")

        if 'TELEGRAM_BOT_TOKEN' not in env_vars:
            self.error("Cannot test Telegram API: TELEGRAM_BOT_TOKEN not configured")
            return False

        bot_token = env_vars['TELEGRAM_BOT_TOKEN']

        try:
            # Test bot token validity
            url = f"https://api.telegram.org/bot{bot_token}/getMe"

            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())

            if data.get('ok'):
                bot_info = data.get('result', {})
                self.success("Telegram Bot API connection successful")
                self.info(f"Bot name: {bot_info.get('first_name', 'Unknown')}")
                self.info(f"Bot username: @{bot_info.get('username', 'Unknown')}")
                return True
            else:
                self.error(f"Telegram API error: {data.get('description', 'Unknown error')}")
                return False

        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.error("Telegram bot token is invalid")
            else:
                self.error(f"Telegram API HTTP error {e.code}: {e.reason}")
            return False
        except Exception as e:
            self.error(f"Telegram API test failed: {e}")
            return False

    async def test_telegram_message_sending(self, env_vars: Dict[str, str]) -> bool:
        """Test sending a Telegram message."""
        print("\n💬 Testing Telegram Message Sending...")

        try:
            # Set environment variables
            for key, value in env_vars.items():
                os.environ[key] = value

            from app.services.telegram_service import TelegramService

            telegram_service = TelegramService()

            # Send test message
            result = await telegram_service.send_message("🧪 Configuration validation test - BTC Trading Bot")

            if result:
                self.success("Telegram message sent successfully")
                self.info("Check your Telegram chat for the test message")
                return True
            else:
                self.error("Failed to send Telegram message")
                return False

        except Exception as e:
            self.error(f"Telegram message test failed: {e}")
            self.info("Make sure TELEGRAM_CHAT_ID is set or the bot can detect your chat")
            return False

    def test_coinbase_api(self) -> bool:
        """Test Coinbase API connectivity (public endpoints)."""
        print("\n₿ Testing Coinbase API...")

        try:
            # Test public API endpoint
            url = "https://api.exchange.coinbase.com/products/BTC-USD/ticker"

            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())

            if 'price' in data:
                self.success("Coinbase public API accessible")
                self.info(f"Current BTC price: ${float(data['price']):,.2f}")
                return True
            else:
                self.warning("Coinbase API response format unexpected")
                return False

        except Exception as e:
            self.warning(f"Coinbase API test failed: {e}")
            self.info("This is not critical - the bot can still function with cached data")
            return False

    def validate_data_directories(self) -> bool:
        """Validate data directory structure."""
        print("\n📁 Validating Data Directories...")

        required_dirs = [
            'data',
            'data/logs',
            'data/state',
            'data/history',
            'data/cache',
            'data/backups'
        ]

        all_exist = True
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                self.error(f"Missing directory: {dir_path}")
                self.info(f"Create with: mkdir -p {dir_path}")
                all_exist = False
            else:
                if full_path.is_dir():
                    self.success(f"Directory exists: {dir_path}")
                else:
                    self.error(f"Path exists but is not a directory: {dir_path}")
                    all_exist = False

        return all_exist

    def print_summary(self) -> bool:
        """Print validation summary."""
        print("\n" + "="*60)
        print("📋 CONFIGURATION VALIDATION SUMMARY")
        print("="*60)

        if not self.issues and not self.warnings:
            print("🎉 All validation checks passed!")
            print("\n✅ Your BTC Trading Bot is properly configured and ready to run.")
            print("\n🚀 Next steps:")
            print("   1. Start the application: python -m app.main")
            print("   2. Or use Docker: docker-compose up -d")
            print("   3. Visit the dashboard: http://localhost:8000")
            return True

        if self.issues:
            print(f"\n❌ Found {len(self.issues)} critical issues:")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")

        if self.warnings:
            print(f"\n⚠️  Found {len(self.warnings)} warnings:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        if self.issues:
            print(f"\n❌ Configuration validation failed. Please fix the critical issues above.")
            return False
        else:
            print(f"\n✅ Configuration validation passed with warnings.")
            print("   The bot should work, but consider addressing the warnings above.")
            return True

    async def run_validation(self) -> bool:
        """Run complete configuration validation."""
        print("🔍 BTC Trading Bot - Configuration Validation")
        print("="*60)

        # Load environment variables
        env_vars = self.load_env_file()
        if not env_vars:
            return False

        # Validate configuration
        required_valid = self.validate_required_config(env_vars)
        self.validate_optional_config(env_vars)

        # Validate credentials
        google_creds_valid = self.validate_google_credentials()

        # Validate directories
        dirs_valid = self.validate_data_directories()

        # Test APIs if configuration is valid
        google_api_valid = False
        telegram_api_valid = False
        telegram_msg_valid = False

        if required_valid and google_creds_valid:
            google_api_valid = await self.test_google_sheets_api(env_vars)

        if required_valid:
            telegram_api_valid = self.test_telegram_bot_api(env_vars)
            if telegram_api_valid:
                telegram_msg_valid = await self.test_telegram_message_sending(env_vars)

        # Test optional APIs
        self.test_coinbase_api()

        # Print summary
        return self.print_summary()


async def main():
    """Main validation function."""
    validator = ConfigValidator()
    success = await validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())