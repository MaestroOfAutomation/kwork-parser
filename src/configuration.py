from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    categories: str = os.getenv("KWORK_CATEGORIES", "41")
    poll_interval: int = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    tg_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_chat_id: int = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
