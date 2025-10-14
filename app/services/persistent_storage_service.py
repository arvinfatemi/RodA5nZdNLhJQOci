"""
Persistent storage service for maintaining bot state and history across restarts.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class PersistentStorageService:
    """Service for managing persistent storage of bot data."""

    def __init__(
        self,
        bot_state_file: Optional[str] = None,
        notification_history_file: Optional[str] = None,
    ):
        self.logger = logger
        
        # Use data directory from config
        if bot_state_file is None:
            data_dir = Path(settings.config_cache_path).parent
            data_dir.mkdir(parents=True, exist_ok=True)
            bot_state_file = str(data_dir / "bot_state.json")
            
        if notification_history_file is None:
            data_dir = Path(settings.config_cache_path).parent
            data_dir.mkdir(parents=True, exist_ok=True)
            notification_history_file = str(data_dir / "notification_history.json")
            
        self.bot_state_file = Path(bot_state_file)
        self.notification_history_file = Path(notification_history_file)
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """Ensure all storage files exist with proper initialization."""
        # Bot state file
        if not self.bot_state_file.exists():
            initial_state = {
                "bot_start_time": None,
                "total_uptime_seconds": 0.0,
                "lifetime_stats": {
                    "total_checks": 0,
                    "total_trades": 0,
                    "total_errors": 0,
                    "first_run": datetime.now().isoformat(),
                },
                "daily_resets": [],
                "config_changes": [],
                "created_at": datetime.now().isoformat(),
            }
            self._write_json_file(self.bot_state_file, initial_state)
            self.logger.info(f"Created bot state file: {self.bot_state_file}")

        # Notification history file
        if not self.notification_history_file.exists():
            initial_notifications = {
                "notifications": [],
                "summary": {
                    "total_sent": 0,
                    "total_failed": 0,
                    "last_notification": None,
                    "created_at": datetime.now().isoformat(),
                },
            }
            self._write_json_file(self.notification_history_file, initial_notifications)
            self.logger.info(
                f"Created notification history file: {self.notification_history_file}"
            )

    def _read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Read and parse a JSON file."""
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error reading {file_path}: {e}")
            return {}

    def _write_json_file(self, file_path: Path, data: Dict[str, Any]):
        """Write data to a JSON file."""
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error writing to {file_path}: {e}")
            raise

    def save_bot_state(
        self,
        is_running: bool,
        start_time: Optional[datetime] = None,
        total_checks_today: int = 0,
        total_trades_today: int = 0,
        last_error: Optional[str] = None,
    ):
        """Save current bot state to persistent storage."""
        try:
            state_data = self._read_json_file(self.bot_state_file)

            # Update current session info
            state_data["is_running"] = is_running
            state_data["last_update"] = datetime.now().isoformat()
            state_data["daily_stats"] = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "checks": total_checks_today,
                "trades": total_trades_today,
                "last_error": last_error,
            }

            if start_time:
                state_data["bot_start_time"] = start_time.isoformat()

            # Update lifetime stats
            lifetime_stats = state_data.setdefault("lifetime_stats", {})
            lifetime_stats["total_checks"] = (
                lifetime_stats.get("total_checks", 0) + total_checks_today
            )
            lifetime_stats["total_trades"] = (
                lifetime_stats.get("total_trades", 0) + total_trades_today
            )
            if last_error:
                lifetime_stats["total_errors"] = (
                    lifetime_stats.get("total_errors", 0) + 1
                )

            self._write_json_file(self.bot_state_file, state_data)

        except Exception as e:
            self.logger.error(f"Failed to save bot state: {e}")

    def load_bot_state(self) -> Dict[str, Any]:
        """Load bot state from persistent storage."""
        try:
            return self._read_json_file(self.bot_state_file)
        except Exception as e:
            self.logger.error(f"Failed to load bot state: {e}")
            return {}

    def save_notification(
        self,
        notification_type: str,
        message: str,
        success: bool,
        error: Optional[str] = None,
    ):
        """Save a notification to persistent history."""
        try:
            data = self._read_json_file(self.notification_history_file)

            notification_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": notification_type,
                "message": message,
                "success": success,
                "error": error,
            }

            # Add to notifications list
            notifications = data.setdefault("notifications", [])
            notifications.append(notification_entry)

            # Keep only last 1000 notifications to prevent file from growing too large
            if len(notifications) > 1000:
                notifications = notifications[-1000:]
                data["notifications"] = notifications

            # Update summary
            summary = data.setdefault("summary", {})
            summary["total_sent"] = summary.get("total_sent", 0) + (1 if success else 0)
            summary["total_failed"] = summary.get("total_failed", 0) + (
                0 if success else 1
            )
            summary["last_notification"] = datetime.now().isoformat()

            self._write_json_file(self.notification_history_file, data)

        except Exception as e:
            self.logger.error(f"Failed to save notification: {e}")

    def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent notification history."""
        try:
            data = self._read_json_file(self.notification_history_file)
            notifications = data.get("notifications", [])
            return notifications[-limit:] if notifications else []
        except Exception as e:
            self.logger.error(f"Failed to get notification history: {e}")
            return []

    def record_daily_reset(self):
        """Record a daily reset event."""
        try:
            state_data = self._read_json_file(self.bot_state_file)

            daily_resets = state_data.setdefault("daily_resets", [])
            daily_resets.append(
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Keep only last 30 days
            if len(daily_resets) > 30:
                daily_resets = daily_resets[-30:]
                state_data["daily_resets"] = daily_resets

            self._write_json_file(self.bot_state_file, state_data)

        except Exception as e:
            self.logger.error(f"Failed to record daily reset: {e}")

    def record_config_change(self, old_config: Dict, new_config: Dict):
        """Record a configuration change."""
        try:
            state_data = self._read_json_file(self.bot_state_file)

            config_changes = state_data.setdefault("config_changes", [])
            config_changes.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "old_config": old_config,
                    "new_config": new_config,
                    "changes": self._get_config_changes(old_config, new_config),
                }
            )

            # Keep only last 50 config changes
            if len(config_changes) > 50:
                config_changes = config_changes[-50:]
                state_data["config_changes"] = config_changes

            self._write_json_file(self.bot_state_file, state_data)

        except Exception as e:
            self.logger.error(f"Failed to record config change: {e}")

    def _get_config_changes(self, old_config: Dict, new_config: Dict) -> List[str]:
        """Get a list of configuration changes."""
        changes = []

        for key in new_config:
            if key in old_config and old_config[key] != new_config[key]:
                changes.append(f"{key}: {old_config[key]} → {new_config[key]}")
            elif key not in old_config:
                changes.append(f"{key}: added ({new_config[key]})")

        for key in old_config:
            if key not in new_config:
                changes.append(f"{key}: removed ({old_config[key]})")

        return changes

    def get_lifetime_stats(self) -> Dict[str, Any]:
        """Get lifetime statistics."""
        try:
            state_data = self._read_json_file(self.bot_state_file)
            return state_data.get("lifetime_stats", {})
        except Exception as e:
            self.logger.error(f"Failed to get lifetime stats: {e}")
            return {}

    def get_trading_stats(self) -> Dict[str, Any]:
        """Get trading statistics (alias for lifetime stats for consistency)."""
        stats = self.get_lifetime_stats()
        return {
            "total_checks": stats.get("total_checks", 0),
            "executed_trades": stats.get("total_trades", 0),
            "total_errors": stats.get("total_errors", 0),
        }

    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to prevent storage files from growing too large."""
        try:
            cutoff_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ).timestamp() - (days_to_keep * 24 * 60 * 60)

            # Clean notification history
            data = self._read_json_file(self.notification_history_file)
            notifications = data.get("notifications", [])

            filtered_notifications = []
            for notification in notifications:
                notification_time = datetime.fromisoformat(
                    notification["timestamp"]
                ).timestamp()
                if notification_time >= cutoff_date:
                    filtered_notifications.append(notification)

            if len(filtered_notifications) != len(notifications):
                data["notifications"] = filtered_notifications
                self._write_json_file(self.notification_history_file, data)
                self.logger.info(
                    f"Cleaned {len(notifications) - len(filtered_notifications)} old notifications"
                )

        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")

    def export_all_data(self, output_dir: str = "exports") -> Dict[str, str]:
        """Export all data to files for backup/analysis."""
        try:
            export_path = Path(output_dir)
            export_path.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            exported_files = {}

            # Export bot state
            bot_state_file = export_path / f"bot_state_{timestamp}.json"
            bot_state = self._read_json_file(self.bot_state_file)
            self._write_json_file(bot_state_file, bot_state)
            exported_files["bot_state"] = str(bot_state_file)

            # Export notification history
            notifications_file = export_path / f"notifications_{timestamp}.json"
            notifications = self._read_json_file(self.notification_history_file)
            self._write_json_file(notifications_file, notifications)
            exported_files["notifications"] = str(notifications_file)

            self.logger.info(f"Exported all data to {output_dir}")
            return exported_files

        except Exception as e:
            self.logger.error(f"Failed to export data: {e}")
            return {}


# Global service instance
persistent_storage_service = PersistentStorageService()
