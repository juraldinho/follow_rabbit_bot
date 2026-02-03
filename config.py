import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_id: int


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_id_str = os.getenv("ADMIN_ID", "").strip()

    if not token:
        raise RuntimeError("BOT_TOKEN is missing in .env")

    try:
        admin_id = int(admin_id_str)
    except ValueError:
        raise RuntimeError("ADMIN_ID is missing or not a number in .env")

    return Config(
        bot_token=token,
        admin_id=admin_id,
    )
