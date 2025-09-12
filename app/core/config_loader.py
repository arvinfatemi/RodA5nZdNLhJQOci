"""
Config loader for the Auto Trading Bot (Apziva Project)

- Reads config from a Google Sheet (service account auth).
- Enforces types & validates keys relevant to the project (DCA %, ATR, mode, intervals, toggles).
- Caches to a local JSON file as a fallback when Sheets is unavailable.
- Optional max_age lets you avoid hitting Sheets more than hourly.

Sheet format (worksheet "Config" by default):
------------------------------------------------
| key                      | value         | type | notes (optional) |
------------------------------------------------
| budget_usd               | 10000         | int  |
| dca_drop_pct             | 3             | float|
| dca_buy_amount_usd       | 500           | float|
| atr_period               | 14            | int  |
| atr_multiplier           | 1.5           | float|
| mode                     | hybrid        | enum | dca|swing|hybrid
| data_fetch_interval_min  | 30            | int  |
| enable_dca               | true          | bool |
| enable_swing             | true          | bool |
| enable_telegram          | true          | bool |
| enable_email_reports     | true          | bool |
| report_day               | monday        | enum | monday..sunday
| report_time              | 09:00         | str  | 24h HH:MM
| global_drawdown_pause_pct| 25            | float|

Auth:
- Use a Google service account (JSON key). Do NOT put secrets in the sheet.
- Set one of:
    * GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json
    * GCP_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'  (inline, e.g., from a secrets manager)

Install:
    pip install gspread google-auth
"""

from __future__ import annotations
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict

import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request as GoogleRequest

DEFAULTS = {
    "budget_usd": 10_000,
    "dca_drop_pct": 3.0,
    "dca_buy_amount_usd": 500.0,
    "atr_period": 14,
    "atr_multiplier": 1.5,
    "mode": "hybrid",  # one of: dca | swing | hybrid
    "data_fetch_interval_min": 30,
    "enable_dca": True,
    "enable_swing": True,
    "enable_telegram": True,
    "enable_email_reports": True,
    "report_day": "monday",  # monday..sunday
    "report_time": "09:00",  # 24h
    "global_drawdown_pause_pct": 25.0,
}

VALID_ENUMS = {
    "mode": {"dca", "swing", "hybrid"},
    "report_day": {
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    },
}

TYPE_CASTERS = {
    "int": int,
    "float": float,
    "bool": lambda s: str(s).strip().lower() in {"1", "true", "yes", "y", "on"},
    "str": str,
    "enum": str,  # validated separately when key is known
}

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _now_ts() -> float:
    return time.time()


def _load_google_credentials():
    """Load Google API credentials supporting both Service Account and OAuth client flows.

    Priority:
      1) GCP_SERVICE_ACCOUNT_JSON (inline JSON) — validated and used if type==service_account
      2) GOOGLE_APPLICATION_CREDENTIALS path — service account or OAuth client secrets
      3) GOOGLE_OAUTH_CLIENT_SECRETS or ./credentials.json — OAuth Installed App flow
    Stores/uses OAuth token at GOOGLE_OAUTH_TOKEN_PATH or ./token.json.
    """
    log = logging.getLogger("config_loader")

    # 1) Inline service account JSON
    inline = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if inline:
        try:
            info = json.loads(inline)
            if info.get("type") == "service_account":
                required = {"client_email", "token_uri", "private_key"}
                missing = sorted(required - set(info.keys()))
                if missing:
                    raise ValueError(f"missing fields {', '.join(missing)}")
                return ServiceAccountCredentials.from_service_account_info(
                    info, scopes=SCOPES
                )
            else:
                log.warning(
                    "GCP_SERVICE_ACCOUNT_JSON present but not a service account; ignoring for OAuth flow."
                )
        except Exception as e:
            log.warning(f"Ignoring GCP_SERVICE_ACCOUNT_JSON (invalid): {e}")

    # Helper to run OAuth Installed App flow
    def _oauth_from_client_secrets(client_secrets_path: str, token_path: str):
        creds = None
        if os.path.exists(token_path):
            try:
                creds = UserCredentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                log.warning(f"Ignoring invalid token at {token_path}: {e}")
        if not creds or not creds.valid:
            if creds and creds.expired and getattr(creds, "refresh_token", None):
                try:
                    creds.refresh(GoogleRequest())
                except Exception as e:
                    log.warning(f"Token refresh failed, re-running OAuth flow: {e}")
                    creds = None
            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
                try:
                    with open(token_path, "w", encoding="utf-8") as token:
                        token.write(creds.to_json())
                except Exception as e:
                    log.warning(f"Failed to persist OAuth token at {token_path}: {e}")
        return creds

    # 2) Path via GOOGLE_APPLICATION_CREDENTIALS
    path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("type") == "service_account":
                return ServiceAccountCredentials.from_service_account_info(
                    data, scopes=SCOPES
                )
            # OAuth client secrets
            if "installed" in data or data.get("type") in {"authorized_user", "web"}:
                token_path = os.getenv("GOOGLE_OAUTH_TOKEN_PATH") or os.path.join(
                    os.path.dirname(path), "token.json"
                )
                return _oauth_from_client_secrets(path, token_path)
            # Fallback to library validation for any other shapes
            return ServiceAccountCredentials.from_service_account_file(
                path, scopes=SCOPES
            )
        except Exception as e:
            log.warning(f"Failed loading credentials from {path}: {e}")

    # 3) Explicit OAuth client secrets path or default ./credentials.json
    client_secrets = os.getenv("GOOGLE_OAUTH_CLIENT_SECRETS") or os.path.join(
        os.getcwd(), "credentials.json"
    )
    if os.path.exists(client_secrets):
        token_path = os.getenv("GOOGLE_OAUTH_TOKEN_PATH") or os.path.join(
            os.path.dirname(client_secrets), "token.json"
        )
        try:
            return _oauth_from_client_secrets(client_secrets, token_path)
        except Exception as e:
            log.warning(f"Failed OAuth flow using {client_secrets}: {e}")

    raise RuntimeError(
        "Google credentials not found or invalid. Provide a service account key (GCP_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS) "
        "or OAuth client secrets (GOOGLE_OAUTH_CLIENT_SECRETS or ./credentials.json)."
    )


def _open_worksheet(sheet_id: str, worksheet_name: str):
    creds = _load_google_credentials()
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    return sh.worksheet(worksheet_name)


def _parse_row(key: str, value: str, declared_type: str) -> Any:
    caster = TYPE_CASTERS.get(declared_type)
    if caster is None:
        # Fallback: try to infer
        for t in ("int", "float", "bool", "str"):
            try:
                return TYPE_CASTERS[t](value)
            except Exception:
                continue
        return value  # last resort
    parsed = caster(value)
    return parsed


def _validate_enum(key: str, value: str) -> str:
    if key in VALID_ENUMS and value.lower() not in VALID_ENUMS[key]:
        allowed = "|".join(sorted(VALID_ENUMS[key]))
        raise ValueError(f"Invalid value for '{key}': '{value}'. Allowed: {allowed}")
    return value.lower() if isinstance(value, str) else value


def _write_cache(cache_path: str, payload: Dict[str, Any]) -> None:
    tmp = cache_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    os.replace(tmp, cache_path)


def _read_cache(cache_path: str) -> Dict[str, Any]:
    with open(cache_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _is_cache_fresh(cache_path: str, max_age_seconds: int) -> bool:
    try:
        stat = os.stat(cache_path)
        return (_now_ts() - stat.st_mtime) <= max_age_seconds
    except FileNotFoundError:
        return False


def _merge_with_defaults(cfg: Dict[str, Any]) -> Dict[str, Any]:
    merged = DEFAULTS.copy()
    merged.update(cfg)
    return merged


def read_app_config_from_sheet(
    sheet_id: str,
    worksheet_name: str = "Config",
    *,
    cache_path: str = "G:/Codes/bitcoin-trading-agent/config_cache.json",
    use_cache_if_recent: bool = True,
    max_age_seconds: int = 3600,  # 1 hour, aligns with “pull hourly”
    required_keys: set[str] | None = None,
    logger: logging.Logger | None = None,
) -> Dict[str, Any]:
    """
    Load config with priority:
        1) fresh local cache (if use_cache_if_recent)
        2) Google Sheet (service account)
        3) stale/any cache
        4) hardcoded DEFAULTS

    Returns:
        dict with keys + metadata:
            _meta: {source, fetched_at_iso}
    Raises:
        RuntimeError if required_keys missing and cannot be satisfied even with defaults.
    """
    log = logger or logging.getLogger("config_loader")
    required_keys = set(required_keys or [])

    # (1) Use fresh cache if allowed
    if use_cache_if_recent and _is_cache_fresh(cache_path, max_age_seconds):
        try:
            cached = _read_cache(cache_path)
            cfg = _merge_with_defaults(cached.get("config", {}))
            _check_required(cfg, required_keys)
            cfg["_meta"] = {
                "source": "cache:fresh",
                "fetched_at_iso": cached.get("fetched_at_iso"),
            }
            return cfg
        except Exception as e:
            log.warning(f"Ignoring cache (read/parse error): {e}")

    # (2) Try Google Sheet
    try:
        ws = _open_worksheet(sheet_id, worksheet_name)
        rows = ws.get_all_records()  # expects headers: key,value,type,*
        parsed: Dict[str, Any] = {}
        for r in rows:
            key = str(r.get("key", "")).strip()
            if not key:
                continue
            value_raw = str(r.get("value", "")).strip()
            declared_type = str(r.get("type", "str")).strip().lower()
            try:
                val = _parse_row(key, value_raw, declared_type)
                # enum validation (only for known enums)
                if declared_type == "enum" or key in VALID_ENUMS:
                    val = _validate_enum(key, val)
                parsed[key] = val
            except Exception as e:
                log.warning(f"Row parse skipped for key='{key}': {e}")

        cfg = _merge_with_defaults(parsed)
        _check_required(cfg, required_keys)

        payload = {
            "config": {k: v for k, v in cfg.items() if not k.startswith("_")},
            "fetched_at_iso": datetime.utcnow().isoformat() + "Z",
        }
        _write_cache(cache_path, payload)

        cfg["_meta"] = {"source": "sheet", "fetched_at_iso": payload["fetched_at_iso"]}
        return cfg
    except Exception as e:
        log.error(
            f"Failed to read from Google Sheet, falling back to cache/defaults: {e}"
        )

    # (3) Any cache (stale is okay)
    try:
        cached = _read_cache(cache_path)
        cfg = _merge_with_defaults(cached.get("config", {}))
        _check_required(cfg, required_keys)
        cfg["_meta"] = {
            "source": "cache:stale",
            "fetched_at_iso": cached.get("fetched_at_iso"),
        }
        return cfg
    except Exception as e:
        log.warning(f"No usable cache found: {e}")

    # (4) Defaults (last resort)
    cfg = DEFAULTS.copy()
    _check_required(cfg, required_keys)
    cfg["_meta"] = {
        "source": "defaults",
        "fetched_at_iso": datetime.utcnow().isoformat() + "Z",
    }
    return cfg


def _check_required(cfg: Dict[str, Any], required_keys: set[str]) -> None:
    missing = [
        k for k in required_keys if k not in cfg or cfg[k] is None or cfg[k] == ""
    ]
    if missing:
        raise RuntimeError(f"Missing required config keys: {missing}")
