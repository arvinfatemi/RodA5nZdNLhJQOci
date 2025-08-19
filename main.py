import logging
import os, json
from dotenv import load_dotenv, dotenv_values, find_dotenv
from config_loader import read_app_config_from_sheet


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

    cfg = read_app_config_from_sheet(
        sheet_id=sheet_id,
        worksheet_name=worksheet_name,
        cache_path=cache_path,
        use_cache_if_recent=True,
    )

    print(json.dumps(cfg, indent=2))

if __name__ == "__main__":
    main()
