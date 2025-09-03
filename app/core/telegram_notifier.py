import json
import os
import time
import logging
from typing import Any, Dict, List, Optional
from urllib import request, error, parse
from dotenv import dotenv_values, find_dotenv, set_key


TELEGRAM_API_BASE = "https://api.telegram.org"
MAX_MESSAGE_LEN = 4096  # Telegram limit for sendMessage


class TelegramNotifyError(RuntimeError):
    pass


def _chunk_text(text: str, limit: int = MAX_MESSAGE_LEN) -> List[str]:
    if len(text) <= limit:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks


def _load_env_values(env_path: Optional[str] = None) -> (str, Dict[str, str]):
    """Load key-values from a .env file without relying on process env.

    Returns a tuple of (resolved_env_path, values_dict). If no file is found,
    returns (env_path_or_default, {}).
    """
    if env_path and os.path.exists(env_path):
        return env_path, dotenv_values(env_path)
    auto = find_dotenv(usecwd=True)
    if auto:
        return auto, dotenv_values(auto)
    # Fallback to provided path or default .env
    env_path = env_path or ".env"
    if os.path.exists(env_path):
        return env_path, dotenv_values(env_path)
    return env_path, {}


def send_telegram_message(
    text: str,
    *,
    chat_id: Optional[str] = None,
    token: Optional[str] = None,
    parse_mode: Optional[str] = None,  # e.g., "MarkdownV2" or "HTML"
    disable_notification: bool = False,
    timeout: float = 10.0,
    retries: int = 2,
    logger: Optional[logging.Logger] = None,
    env_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Send a Telegram Bot API message using sendMessage.

    - Reads defaults from env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
    - Splits messages longer than 4096 chars into multiple sends.
    - Returns the list of response payloads from Telegram.

    Raises TelegramNotifyError on persistent failures.
    """
    log = logger or logging.getLogger("telegram_notifier")
    env_real_path, env_vals = _load_env_values(env_path)
    token = token or env_vals.get("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise TelegramNotifyError("Missing Telegram bot token (TELEGRAM_BOT_TOKEN)")

    chat_id = chat_id or env_vals.get("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise TelegramNotifyError("Missing Telegram chat id (TELEGRAM_CHAT_ID) or chat_id argument")

    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    headers = {"Content-Type": "application/json"}
    results: List[Dict[str, Any]] = []

    for idx, chunk in enumerate(_chunk_text(text)):
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "disable_notification": disable_notification,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        body = json.dumps(payload).encode("utf-8")
        attempt = 0
        backoff = 1.0
        last_err: Optional[BaseException] = None

        while attempt <= retries:
            attempt += 1
            try:
                req = request.Request(url, data=body, headers=headers, method="POST")
                with request.urlopen(req, timeout=timeout) as resp:
                    data = resp.read()
                    try:
                        parsed = json.loads(data.decode("utf-8"))
                    except Exception:
                        parsed = {"ok": False, "error": "non-json-response", "raw": data.decode("utf-8", "replace")}
                    if not parsed.get("ok", False):
                        # Telegram returns ok=false with description
                        desc = parsed.get("description") or parsed.get("error") or "unknown"
                        raise TelegramNotifyError(f"Telegram API error: {desc}")
                    results.append(parsed)
                    break  # success for this chunk
            except error.HTTPError as e:
                # Avoid logging token; don't print full URL
                msg = f"HTTP {e.code} from Telegram: {getattr(e, 'reason', '')}"
                log.warning(msg)
                last_err = e
            except error.URLError as e:
                log.warning(f"Network error contacting Telegram: {e}")
                last_err = e
            except Exception as e:
                log.warning(f"Unexpected error sending Telegram message: {e}")
                last_err = e

            if attempt <= retries:
                time.sleep(backoff)
                backoff = min(backoff * 2, 8.0)
        else:
            # Retries exhausted for this chunk
            raise TelegramNotifyError(f"Failed to send Telegram message after {retries} retries: {last_err}")

    return results


def _http_get(url: str, timeout: float = 10.0) -> Dict[str, Any]:
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {"ok": False, "error": "non-json-response", "raw": raw.decode("utf-8", "replace")}


def _fetch_updates(token: str, *, timeout: float = 10.0, limit: int = 50) -> List[Dict[str, Any]]:
    # Long polling timeout is server-side seconds; we keep client timeout modest
    params = {"timeout": 0, "limit": limit}
    url = f"{TELEGRAM_API_BASE}/bot{token}/getUpdates?{parse.urlencode(params)}"
    data = _http_get(url, timeout=timeout)
    if not data.get("ok", False):
        desc = data.get("description") or data.get("error") or "unknown"
        raise TelegramNotifyError(f"getUpdates failed: {desc}")
    return data.get("result", []) or []


def _extract_chat_candidates(updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    def _push(chat: Dict[str, Any], src: str) -> None:
        if not chat:
            return
        cid = chat.get("id")
        ctype = chat.get("type")
        title = chat.get("title") or chat.get("username") or ""
        if cid is None:
            return
        candidates.append({"id": cid, "type": ctype, "title": title, "_src": src})

    for upd in updates:
        # Common message containers
        for key in ("message", "edited_message", "channel_post", "edited_channel_post"):
            msg = upd.get(key)
            if msg and isinstance(msg, dict):
                _push(msg.get("chat", {}), key)
        # Membership updates can include chat
        for key in ("my_chat_member", "chat_member", "chat_join_request"):
            obj = upd.get(key)
            if obj and isinstance(obj, dict):
                _push(obj.get("chat", {}), key)
    # Deduplicate by id preserving order
    seen = set()
    uniq: List[Dict[str, Any]] = []
    for c in candidates:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        uniq.append(c)
    return uniq


def _choose_chat_id(
    candidates: List[Dict[str, Any]],
    *,
    prefer_username_or_title: Optional[str] = None,
    prefer_type: Optional[str] = None,  # e.g. "private", "group", "supergroup", "channel"
) -> Optional[int]:
    if not candidates:
        return None
    if prefer_username_or_title:
        want = prefer_username_or_title.lstrip("@").lower()
        for c in candidates:
            title = str(c.get("title") or "").lstrip("@").lower()
            if title == want:
                return int(c["id"])
    if prefer_type:
        for c in candidates:
            if c.get("type") == prefer_type:
                return int(c["id"])
    # Default: first candidate
    return int(candidates[0]["id"])


def _update_env_file(env_path: str, key: str, value: str) -> None:
    # Minimal in-place update with atomic replace
    existing = ""
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            existing = f.read()
    except FileNotFoundError:
        existing = ""

    lines = existing.splitlines()
    updated = False
    new_lines: List[str] = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        new_lines.append(f"{key}={value}")

    tmp = env_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    os.replace(tmp, env_path)


def resolve_and_cache_chat_id(
    *,
    token: Optional[str] = None,
    chat_username_or_title: Optional[str] = None,
    prefer_type: Optional[str] = None,
    env_path: str = ".env",
    timeout: float = 10.0,
) -> int:
    """
    Resolve TELEGRAM_CHAT_ID, fetching from Bot API if missing, and persist to .env.

    Steps:
      - If TELEGRAM_CHAT_ID present in env, return it (no file write).
      - Else call getUpdates, extract chat candidates, pick best match, update .env.
      - Requires at least one message or membership update involving the bot.

    Tips:
      - For private chats: send any message to your bot first.
      - For groups/channels: add the bot and send a message.
    """
    env_real_path, env_vals = _load_env_values(env_path)
    env_chat = env_vals.get("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
    if env_chat:
        try:
            return int(env_chat)
        except Exception:
            pass

    token = token or env_vals.get("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise TelegramNotifyError("Missing TELEGRAM_BOT_TOKEN for resolving chat id")

    updates = _fetch_updates(token, timeout=timeout)
    candidates = _extract_chat_candidates(updates)
    if not candidates:
        raise TelegramNotifyError(
            "No chat candidates found. Send a message to the bot or add it to the target group/channel, then retry."
        )
    chat_id = _choose_chat_id(
        candidates,
        prefer_username_or_title=chat_username_or_title or env_vals.get("TELEGRAM_CHAT_USERNAME") or os.getenv("TELEGRAM_CHAT_USERNAME"),
        prefer_type=prefer_type,
    )
    if chat_id is None:
        raise TelegramNotifyError("Unable to determine chat id from updates")

    # Persist to .env for future runs
    try:
        # Use python-dotenv to update or insert the key
        set_key(env_real_path or env_path, "TELEGRAM_CHAT_ID", str(chat_id))
    except Exception as e:
        logging.getLogger("telegram_notifier").warning(f"Failed to update {env_path}: {e}")

    return chat_id


if __name__ == "__main__":
    # Minimal CLI for manual testing:
    #   python telegram_notifier.py --chat-id 123456789 --text "Hello"
    # Or resolve and cache chat id:
    #   python telegram_notifier.py --resolve-chat-id
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = argparse.ArgumentParser(description="Telegram Bot helper")
    p.add_argument("--chat-id", dest="chat_id", default=None, help="Target chat id")
    p.add_argument("--token", dest="token", default=None, help="Bot token (optional; else env)")
    p.add_argument("--text", dest="text", default=None, help="Message text to send")
    p.add_argument("--parse-mode", dest="parse_mode", default=None, help="Parse mode: MarkdownV2 or HTML")
    p.add_argument("--silent", dest="silent", action="store_true", help="Disable notification")
    p.add_argument("--resolve-chat-id", dest="resolve", action="store_true", help="Resolve chat id via getUpdates and update .env")
    p.add_argument("--prefer", dest="prefer", default=None, help="Preferred chat username/title (e.g., @mychannel)")
    p.add_argument("--prefer-type", dest="prefer_type", default=None, help="Preferred chat type: private|group|supergroup|channel")
    p.add_argument("--env-path", dest="env_path", default=".env", help="Path to .env to update")
    args = p.parse_args()

    try:
        if args.resolve:
            cid = resolve_and_cache_chat_id(
                token=args.token,
                chat_username_or_title=args.prefer,
                prefer_type=args.prefer_type,
                env_path=args.env_path,
            )
            print("Resolved TELEGRAM_CHAT_ID:", cid)
        if args.text is not None:
            resp = send_telegram_message(
                args.text,
                chat_id=args.chat_id,
                token=args.token,
                parse_mode=args.parse_mode,
                disable_notification=args.silent,
            )
            ids = [r.get("result", {}).get("message_id") for r in resp]
            print("Sent", len(resp), "message chunk(s)", "IDs:", ids)
        if not args.resolve and args.text is None:
            print("Nothing to do. Provide --text to send or --resolve-chat-id to resolve.")
    except TelegramNotifyError as e:
        logging.error(str(e))
        raise SystemExit(2)
