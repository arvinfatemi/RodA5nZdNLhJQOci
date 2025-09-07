import logging
import os, sys, json, time, argparse, threading
from dotenv import load_dotenv, dotenv_values, find_dotenv
from config_loader import read_app_config_from_sheet
from ws_client import connect_coinbase_ws


def load_env_values() -> dict:
    # Load environment variables from .env (fallback to .env.txt)
    loaded_path = find_dotenv(usecwd=True)
    values = {}
    if loaded_path:
        load_dotenv(loaded_path, override=False)
        values = dotenv_values(loaded_path)
    elif os.path.exists(".env"):
        load_dotenv(".env", override=False)
        values = dotenv_values(".env")
    elif os.path.exists(".env.txt"):
        load_dotenv(".env.txt", override=False)
        values = dotenv_values(".env.txt")
    return values


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    env_values = load_env_values()

    parser = argparse.ArgumentParser(description="Smart BTC Trading Bot runner")
    parser.add_argument("--ws-only", action="store_true", help="Skip Google Sheet config fetch; start WebSocket only")
    parser.add_argument("--granularity", default=None, help="Candles granularity (e.g., 30m, 1m, 1h, or seconds like 1800)")
    parser.add_argument("--duration", type=int, default=None, help="Auto-stop after N seconds (for testing)")
    parser.add_argument("--force-exit", action="store_true", help="Forcefully terminate the process after stopping WS")
    parser.add_argument("--ws-backend", choices=["sdk", "raw"], default="raw", help="Choose WebSocket backend: coinbase SDK or raw websockets")
    parser.add_argument("--verify-data", action="store_true", help="Verify that some data arrives within timeout, then exit")
    parser.add_argument("--verify-timeout", type=int, default=15, help="Seconds to wait for first data when --verify-data is set")
    parser.add_argument("--require-all", action="store_true", help="When verifying, require ticker+candles+heartbeat before success")
    args = parser.parse_args()

    # Resolve Google Sheet parameters from env or env file
    # sheet_id = (
    #     os.getenv("GOOGLE_SHEET_ID")
    #     or os.getenv("SHEET_ID")
    #     or env_values.get("GOOGLE_SHEET_ID")
    #     or env_values.get("SHEET_ID")
    # )
    # worksheet_name = os.getenv("WORKSHEET_NAME", env_values.get("WORKSHEET_NAME", "Config"))
    sheet_id = '1A58QwxlFcy2zJGfcPRlBLtlaoC7eundbS6DpG24nMao'
    worksheet_name = 'Sheet1'

    # Use a portable cache path next to this file
    here = os.path.dirname(os.path.abspath(__file__))
    cache_path = os.path.join(here, "config_cache.json")

    if not sheet_id:
        logging.error(
            "Missing GOOGLE_SHEET_ID (or SHEET_ID). Set it in .env or environment."
        )
        return

    if not args.ws_only:
        # Try to fetch config, but do not block WS testing if it fails
        try:
            cfg = read_app_config_from_sheet(
                sheet_id=sheet_id,
                worksheet_name=worksheet_name,
                cache_path=cache_path,
                use_cache_if_recent=True,
            )
            print(json.dumps(cfg, indent=2))
        except Exception as e:
            logging.warning(f"Config load failed, continuing to WS test: {e}")
    else:
        logging.info("--ws-only set: skipping Google Sheet config fetch")

    # Start Coinbase WebSocket for BTC-USD with ticker, candles, heartbeat
    got_any = threading.Event()
    got_ticker = threading.Event()
    got_candle = threading.Event()
    got_heartbeat = threading.Event()

    def _mark_any():
        try:
            got_any.set()
        except Exception:
            pass
    def on_ticker(msg: dict):
        print("ticker:", json.dumps(msg, separators=(",", ":"), indent=2))
        got_ticker.set(); _mark_any()

    def on_candle(msg: dict):
        print("candle:", json.dumps(msg, separators=(",", ":"), indent=2))
        got_candle.set(); _mark_any()

    def on_heartbeat(msg: dict):
        # Keep heartbeat concise
        print("heartbeat:", json.dumps({k: msg.get(k) for k in ("channel", "product_id", "time", "sequence")}, separators=(",", ":"), indent=2))
        got_heartbeat.set(); _mark_any()

    granularity = (
        args.granularity
        if args.granularity is not None
        else os.getenv("COINBASE_CANDLES_GRANULARITY", env_values.get("COINBASE_CANDLES_GRANULARITY", "30m"))
    )
    print(f"Starting WS backend: {args.ws_backend}")
    client = connect_coinbase_ws(
        products=["BTC-USD"],
        granularity=granularity,
        on_ticker=on_ticker,
        on_candle=on_candle,
        on_heartbeat=on_heartbeat,
        use_sdk_preferred=(args.ws_backend == "sdk"),
    )

    print("WebSocket started. Press Ctrl+C or press 'q' then Enter to stop.")
    if args.verify_data:
        print(f"Verifying data arrival (timeout {args.verify_timeout}s, require_all={args.require_all})...")
        start = time.time()
        ok = False
        try:
            while (time.time() - start) <= args.verify_timeout:
                time.sleep(0.1)
                if args.require_all:
                    if got_ticker.is_set() and got_candle.is_set() and got_heartbeat.is_set():
                        ok = True
                        break
                else:
                    if got_any.is_set():
                        ok = True
                        break
        except KeyboardInterrupt:
            pass
        finally:
            client.stop()
        if ok:
            print(
                "OK: Data received:",
                {
                    "ticker": got_ticker.is_set(),
                    "candles": got_candle.is_set(),
                    "heartbeat": got_heartbeat.is_set(),
                },
            )
            sys.exit(0)
        else:
            print("ERROR: No data received within timeout")
            sys.exit(2)
    if args.duration:
        print(f"Auto-stopping after {args.duration}s (testing mode)")
    try:
        # Allow both Ctrl+C and 'q'+Enter to stop
        start_time = time.time()
        while True:
            time.sleep(0.5)
            if args.duration and (time.time() - start_time) >= args.duration:
                print("Duration reached. Stopping WebSocket...")
                break
            try:
                # Windows-friendly non-blocking keypress check
                import msvcrt  # type: ignore

                if msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    if ch.lower() == 'q':
                        print("'q' received. Stopping WebSocket...")
                        break
            except Exception:
                # On non-Windows or if unavailable, ignore and rely on Ctrl+C
                pass
    except KeyboardInterrupt:
        print("Stopping WebSocket...")
    finally:
        client.stop()
        # Give a brief moment for background threads to wind down
        time.sleep(0.5)
        if args.force_exit:
            print("Force exiting process...")
            os._exit(0)
        # Ensure we terminate even if a non-daemon thread lingers
        sys.exit(0)

if __name__ == "__main__":
    main()
