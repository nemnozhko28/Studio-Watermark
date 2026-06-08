import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    api_id: int
    api_hash: str
    admin_id: int
    admin_channel_id: int
    database_url: str
    max_workers: int = 2
    temp_dir: str = "bot/temp"
    fonts_dir: str = "bot/fonts"
    logs_dir: str = "bot/logs"


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN is not set in environment variables")

    api_id = os.getenv("API_ID")
    if not api_id:
        raise ValueError("API_ID is not set in environment variables")

    api_hash = os.getenv("API_HASH")
    if not api_hash:
        raise ValueError("API_HASH is not set in environment variables")

    admin_id = os.getenv("ADMIN_ID")
    if not admin_id:
        raise ValueError("ADMIN_ID is not set in environment variables")

    admin_channel_id = os.getenv("ADMIN_CHANNEL_ID")
    if not admin_channel_id:
        raise ValueError("ADMIN_CHANNEL_ID is not set in environment variables")

    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot/watermark_bot.db")

    return Config(
        bot_token=bot_token,
        api_id=int(api_id),
        api_hash=api_hash,
        admin_id=int(admin_id),
        admin_channel_id=int(admin_channel_id),
        database_url=database_url,
        max_workers=int(os.getenv("MAX_WORKERS", "2")),
    )


config = load_config()

SUPPORTED_VIDEO_FORMATS = {"mp4", "mov", "mkv", "avi", "webm"}

FONTS = {
    "Montserrat-Bold": "bot/fonts/Montserrat-Bold.ttf",
    "Arial": "bot/fonts/Arial.ttf",
    "Roboto": "bot/fonts/Roboto-Regular.ttf",
}

SIZES = ["2%", "4%", "6%", "8%", "10%", "12%", "15%", "20%"]

COLORS = ["white", "black", "red", "green", "blue", "yellow", "orange", "gray"]

OPACITIES = ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0"]

POSITIONS = {
    "left_top": "Лев.верх",
    "center_top": "Центр верх",
    "right_top": "Прав.верх",
    "left_center": "Лев.центр",
    "center": "Центр",
    "right_center": "Прав.центр",
    "left_bottom": "Лев.низ",
    "center_bottom": "Центр низ",
    "right_bottom": "Прав.низ",
}

TELEGRAM_FILE_LIMIT = 50 * 1024 * 1024  # 50 MB — send_video limit
TELEGRAM_DOCUMENT_LIMIT = 2 * 1024 * 1024 * 1024  # 2 GB
