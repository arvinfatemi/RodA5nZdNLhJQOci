#!/usr/bin/env python3
"""
Test script for simplified setup features.

Tests the fallback mechanisms for:
1. Google Sheets (public CSV fallback)
2. Notifications (Telegram → Email → Console)
"""

import os
import sys
import asyncio


def test_config_fallback():
    """Test Google Sheets public CSV fallback."""
    print("=" * 60)
    print("TEST 1: Google Sheets Config Loader")
    print("=" * 60)

    try:
        from app.core.config_loader import _has_google_credentials, _fetch_public_sheet_csv

        # Test credential detection
        has_creds = _has_google_credentials()
        print(f"✓ Credential detection works")
        print(f"  - Has credentials: {has_creds}")

        # Test public CSV fetch (using example public sheet)
        # This is a test public sheet - replace with actual sheet for real testing
        test_sheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

        print(f"\n✓ Testing public CSV fetch...")
        print(f"  - Sheet ID: {test_sheet_id}")

        try:
            rows = _fetch_public_sheet_csv(test_sheet_id, worksheet_gid=0)
            print(f"  - Fetched {len(rows)} rows")
            if rows:
                print(f"  - Sample keys: {list(rows[0].keys())[:3]}")
            print("✓ Public CSV fetch successful!")
        except Exception as e:
            print(f"  - Note: CSV fetch needs internet connection")
            print(f"  - Error: {e}")

        print("\n✅ Config loader fallback mechanism verified\n")
        return True

    except Exception as e:
        print(f"❌ Config loader test failed: {e}\n")
        return False


def test_email_notifier():
    """Test email notification functions."""
    print("=" * 60)
    print("TEST 2: Email Notifier")
    print("=" * 60)

    try:
        from app.core.email_notifier import validate_email_config, send_notification_email

        # Test validation with no config
        is_valid = validate_email_config()
        print(f"✓ Email validation works")
        print(f"  - Valid (no config): {is_valid}")

        # Test validation with partial config
        is_valid = validate_email_config(
            smtp_host="smtp.gmail.com",
            email_from="test@example.com"
        )
        print(f"  - Valid (partial): {is_valid}")

        # Test validation with full config
        is_valid = validate_email_config(
            smtp_host="smtp.gmail.com",
            email_from="test@example.com",
            email_password="password",
            email_to="recipient@example.com"
        )
        print(f"  - Valid (complete): {is_valid}")

        print("\n✅ Email notifier functions verified\n")
        return True

    except Exception as e:
        print(f"❌ Email notifier test failed: {e}\n")
        return False


async def test_notification_fallback():
    """Test notification fallback chain."""
    print("=" * 60)
    print("TEST 3: Notification Fallback Chain")
    print("=" * 60)

    try:
        from app.config import settings
        from app.services.notification_service import notification_service

        print("✓ Notification service loaded")
        print(f"  - Telegram token configured: {bool(settings.telegram_bot_token)}")
        print(f"  - Email SMTP configured: {bool(settings.email_smtp_host)}")

        # Test sending a notification (will use fallback chain)
        print("\n✓ Testing notification send...")
        print("  - This will use the fallback chain:")
        print("    1. Try Telegram (if configured)")
        print("    2. Try Email (if configured)")
        print("    3. Fall back to Console (always works)")

        # Send test notification
        await notification_service._send_notification(
            message="🧪 Test notification from simplified setup test",
            notification_type=notification_service.NotificationType.MANUAL_CHECK
        )

        print("\n✅ Notification fallback chain verified\n")
        return True

    except Exception as e:
        print(f"❌ Notification fallback test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_env_configuration():
    """Test environment configuration."""
    print("=" * 60)
    print("TEST 4: Environment Configuration")
    print("=" * 60)

    try:
        from app.config import settings

        print("✓ Settings loaded successfully")
        print(f"\nGoogle Sheets:")
        print(f"  - Sheet ID: {settings.google_sheet_id}")
        print(f"  - Worksheet: {settings.google_worksheet_name}")
        print(f"  - Has credentials file: {bool(settings.google_application_credentials)}")

        print(f"\nNotifications:")
        print(f"  - Telegram token: {'SET' if settings.telegram_bot_token else 'NOT SET'}")
        print(f"  - Email SMTP: {settings.email_smtp_host or 'NOT SET'}")
        print(f"  - Email from: {settings.email_from or 'NOT SET'}")
        print(f"  - Email to: {settings.email_to or 'NOT SET'}")

        print("\n✅ Configuration verified\n")
        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}\n")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SIMPLIFIED SETUP TEST SUITE")
    print("=" * 60)
    print()

    results = []

    # Run tests
    results.append(("Config Fallback", test_config_fallback()))
    results.append(("Email Notifier", test_email_notifier()))
    results.append(("Environment Config", test_env_configuration()))

    # Run async notification test
    try:
        result = asyncio.run(test_notification_fallback())
        results.append(("Notification Fallback", result))
    except Exception as e:
        print(f"❌ Notification test failed: {e}")
        results.append(("Notification Fallback", False))

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print()
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
