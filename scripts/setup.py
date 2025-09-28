#!/usr/bin/env python3
"""
BTC Trading Bot Setup and Validation Script

This script helps validate the setup and configuration of the BTC Trading Bot.
It checks dependencies, validates configuration, and tests external service connectivity.
"""

import asyncio
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class SetupValidator:
    """Main setup validation class."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.success_count = 0
        self.total_checks = 0

    def print_header(self):
        """Print setup validation header."""
        print(f"{Colors.BLUE}{Colors.BOLD}=" * 60)
        print("    BTC Trading Bot - Setup Validation")
        print("=" * 60 + Colors.END)
        print()

    def print_section(self, title: str):
        """Print section header."""
        print(f"{Colors.BOLD}{title}{Colors.END}")
        print("-" * len(title))

    def check_result(self, description: str, success: bool, details: str = "") -> bool:
        """Print check result and track success/failure."""
        self.total_checks += 1
        if success:
            self.success_count += 1
            status = f"{Colors.GREEN}✓{Colors.END}"
        else:
            status = f"{Colors.RED}✗{Colors.END}"
            self.errors.append(f"{description}: {details}")

        print(f"{status} {description}")
        if details and not success:
            print(f"   {Colors.RED}{details}{Colors.END}")
        elif details and success:
            print(f"   {Colors.GREEN}{details}{Colors.END}")

        return success

    def warn(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
        print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

    def check_python_version(self) -> bool:
        """Check Python version compatibility."""
        self.print_section("Python Environment")

        version = sys.version_info
        success = version >= (3, 10)
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        if success:
            details = f"Python {version_str} (✓ >= 3.10)"
        else:
            details = f"Python {version_str} (✗ requires >= 3.10)"

        return self.check_result("Python version", success, details)

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        print()
        self.print_section("Dependencies")

        # Check if we're in a virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        self.check_result("Virtual environment", in_venv,
                         "Active" if in_venv else "Not detected (recommended)")

        # Check required packages
        required_packages = [
            'fastapi', 'uvicorn', 'pydantic-settings', 'gspread',
            'google-auth', 'requests', 'websocket-client', 'APScheduler'
        ]

        all_installed = True
        missing_packages = []

        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                success = True
                details = "Installed"
            except ImportError:
                success = False
                details = "Missing"
                all_installed = False
                missing_packages.append(package)

            self.check_result(f"Package: {package}", success, details)

        if missing_packages:
            print(f"\n{Colors.YELLOW}To install missing packages:{Colors.END}")
            print(f"pip install {' '.join(missing_packages)}")

        return all_installed

    def check_project_structure(self) -> bool:
        """Check if project structure is correct."""
        print()
        self.print_section("Project Structure")

        required_dirs = [
            'app', 'app/api', 'app/services', 'app/models',
            'docs', 'scripts', 'tools', 'tests', 'data'
        ]
        required_files = [
            'app/main.py', 'app/config.py', '.env.example',
            'requirements.txt', 'Dockerfile', 'docker-compose.yml'
        ]

        all_present = True

        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            exists = full_path.exists() and full_path.is_dir()
            if not exists:
                all_present = False
            self.check_result(f"Directory: {dir_path}", exists)

        for file_path in required_files:
            full_path = self.project_root / file_path
            exists = full_path.exists() and full_path.is_file()
            if not exists:
                all_present = False
            self.check_result(f"File: {file_path}", exists)

        return all_present

    def check_environment_config(self) -> Tuple[bool, Dict]:
        """Check environment configuration."""
        print()
        self.print_section("Environment Configuration")

        env_file = self.project_root / '.env'
        env_example = self.project_root / '.env.example'

        # Check if .env exists
        env_exists = env_file.exists()
        self.check_result(".env file exists", env_exists)

        if not env_exists and env_example.exists():
            self.warn("Copy .env.example to .env and configure it")
            return False, {}

        if not env_exists:
            return False, {}

        # Load environment variables
        env_vars = {}
        try:
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        except Exception as e:
            self.check_result("Environment file readable", False, str(e))
            return False, {}

        # Check required variables
        required_vars = ['GOOGLE_SHEET_ID', 'TELEGRAM_BOT_TOKEN']
        optional_vars = ['TELEGRAM_CHAT_ID', 'DEBUG', 'HOST', 'PORT']

        config_valid = True
        for var in required_vars:
            present = var in env_vars and env_vars[var]
            if not present:
                config_valid = False
            self.check_result(f"Required: {var}", present,
                             "Set" if present else "Missing")

        for var in optional_vars:
            present = var in env_vars
            self.check_result(f"Optional: {var}", True,
                             f"Set ({env_vars[var]})" if present else "Not set")

        return config_valid, env_vars

    def check_google_credentials(self) -> bool:
        """Check Google credentials setup."""
        print()
        self.print_section("Google Credentials")

        service_account = self.project_root / 'service_account.json'
        token_file = self.project_root / 'token.json'

        has_service_account = service_account.exists()
        has_token = token_file.exists()

        self.check_result("service_account.json", has_service_account,
                         "Present" if has_service_account else "Missing")
        self.check_result("token.json", has_token,
                         "Present" if has_token else "Missing or will be auto-generated")

        if has_service_account:
            try:
                with open(service_account) as f:
                    creds = json.load(f)
                    required_fields = ['type', 'client_email', 'private_key']
                    valid = all(field in creds for field in required_fields)
                    self.check_result("Service account format", valid)
                    return valid
            except Exception as e:
                self.check_result("Service account format", False, str(e))
                return False

        return has_service_account or has_token

    async def test_google_sheets_connection(self, env_vars: Dict) -> bool:
        """Test Google Sheets API connection."""
        print()
        self.print_section("Google Sheets Connection")

        if 'GOOGLE_SHEET_ID' not in env_vars:
            self.check_result("Google Sheets test", False, "GOOGLE_SHEET_ID not set")
            return False

        try:
            # Set environment variables for the test
            for key, value in env_vars.items():
                os.environ[key] = value

            # Import and test config service
            sys.path.insert(0, str(self.project_root))
            from app.services.config_service import ConfigService

            config_service = ConfigService()
            config = await config_service.get_config()

            success = config is not None
            self.check_result("Google Sheets API", success,
                             "Connected successfully" if success else "Connection failed")
            return success

        except Exception as e:
            self.check_result("Google Sheets API", False, str(e))
            return False

    async def test_telegram_connection(self, env_vars: Dict) -> bool:
        """Test Telegram bot connection."""
        print()
        self.print_section("Telegram Bot Connection")

        if 'TELEGRAM_BOT_TOKEN' not in env_vars:
            self.check_result("Telegram test", False, "TELEGRAM_BOT_TOKEN not set")
            return False

        try:
            # Set environment variables for the test
            for key, value in env_vars.items():
                os.environ[key] = value

            # Import and test telegram service
            sys.path.insert(0, str(self.project_root))
            from app.services.telegram_service import TelegramService

            telegram_service = TelegramService()

            # Test with a simple message
            result = await telegram_service.send_message("🧪 BTC Trading Bot setup test successful!")

            success = result is not None
            self.check_result("Telegram Bot API", success,
                             "Message sent successfully" if success else "Failed to send message")
            return success

        except Exception as e:
            self.check_result("Telegram Bot API", False, str(e))
            return False

    def check_docker_setup(self) -> bool:
        """Check Docker setup."""
        print()
        self.print_section("Docker Environment")

        # Check if Docker is installed
        try:
            result = subprocess.run(['docker', '--version'],
                                  capture_output=True, text=True, timeout=10)
            docker_available = result.returncode == 0
            docker_version = result.stdout.strip() if docker_available else "Not installed"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            docker_available = False
            docker_version = "Not installed"

        self.check_result("Docker", docker_available, docker_version)

        # Check Docker Compose
        try:
            result = subprocess.run(['docker-compose', '--version'],
                                  capture_output=True, text=True, timeout=10)
            compose_available = result.returncode == 0
            compose_version = result.stdout.strip() if compose_available else "Not installed"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            compose_available = False
            compose_version = "Not installed"

        self.check_result("Docker Compose", compose_available, compose_version)

        if docker_available and compose_available:
            # Test Docker functionality
            try:
                result = subprocess.run(['docker', 'ps'],
                                      capture_output=True, text=True, timeout=10)
                docker_working = result.returncode == 0
                self.check_result("Docker daemon", docker_working,
                                 "Running" if docker_working else "Not running")
            except subprocess.TimeoutExpired:
                self.check_result("Docker daemon", False, "Timeout")
                docker_working = False
        else:
            docker_working = False

        return docker_available and compose_available and docker_working

    def print_summary(self):
        """Print validation summary."""
        print()
        print(f"{Colors.BOLD}{'=' * 60}")
        print("SETUP VALIDATION SUMMARY")
        print("=" * 60 + Colors.END)

        success_rate = (self.success_count / self.total_checks * 100) if self.total_checks > 0 else 0

        print(f"Total checks: {self.total_checks}")
        print(f"{Colors.GREEN}Passed: {self.success_count}{Colors.END}")
        print(f"{Colors.RED}Failed: {len(self.errors)}{Colors.END}")
        print(f"{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.END}")
        print(f"Success rate: {success_rate:.1f}%")

        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}ERRORS TO FIX:{Colors.END}")
            for i, error in enumerate(self.errors, 1):
                print(f"{Colors.RED}{i}. {error}{Colors.END}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}WARNINGS:{Colors.END}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{Colors.YELLOW}{i}. {warning}{Colors.END}")

        print()
        if len(self.errors) == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}🎉 Setup validation completed successfully!{Colors.END}")
            print(f"{Colors.GREEN}Your BTC Trading Bot is ready to run.{Colors.END}")
            print("\nNext steps:")
            print("1. Start the application: python -m app.main")
            print("2. Or use Docker: docker-compose up -d")
            print("3. Visit: http://localhost:8000")
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ Setup validation failed.{Colors.END}")
            print(f"{Colors.RED}Please fix the errors above before running the bot.{Colors.END}")

        return len(self.errors) == 0

    async def run_validation(self):
        """Run complete setup validation."""
        self.print_header()

        # System checks
        self.check_python_version()
        self.check_dependencies()
        self.check_project_structure()

        # Configuration checks
        config_valid, env_vars = self.check_environment_config()
        self.check_google_credentials()

        # Optional Docker checks
        self.check_docker_setup()

        # External service tests (only if config is valid)
        if config_valid:
            try:
                await self.test_google_sheets_connection(env_vars)
            except Exception as e:
                self.check_result("Google Sheets connection", False, str(e))

            try:
                await self.test_telegram_connection(env_vars)
            except Exception as e:
                self.check_result("Telegram connection", False, str(e))
        else:
            self.warn("Skipping external service tests due to configuration errors")

        # Print summary
        return self.print_summary()


async def main():
    """Main setup validation function."""
    validator = SetupValidator()
    success = await validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())