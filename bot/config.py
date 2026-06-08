import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

_BOT_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(_BOT_DIR)


@dataclass
class Config:
    bot_token: str
    api_id: int
    api_hash: str
    admin_id: int
    admin_channel_id: int
    database_url: str
    session_telethon: str = ""
    max_workers: int = 2
    temp_dir: str = field(default_factory=lambda: os.path.join(_BOT_DIR, "temp"))
    fonts_dir: str = field(default_factory=lambda: os.path.join(_BOT_DIR, "fonts"))
    logs_dir: str = field(default_factory=lambda: os.path.join(_BOT_DIR, "logs"))


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN is not set")

    api_id = os.getenv("API_ID")
    if not api_id:
        raise ValueError("API_ID is not set")

    api_hash = os.getenv("API_HASH")
    if not api_hash:
        raise ValueError("API_HASH is not set")

    admin_id = os.getenv("ADMIN_ID")
    if not admin_id:
        raise ValueError("ADMIN_ID is not set")

    admin_channel_id = os.getenv("ADMIN_CHANNEL_ID")
    if not admin_channel_id:
        raise ValueError("ADMIN_CHANNEL_ID is not set")

    return Config(
        bot_token=bot_token,
        api_id=int(api_id),
        api_hash=api_hash,
        admin_id=int(admin_id),
        admin_channel_id=int(admin_channel_id),
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot/watermark_bot.db"),
        session_telethon=os.getenv("SESSION_TELETHON", ""),
        max_workers=int(os.getenv("MAX_WORKERS", "2")),
    )


config = load_config()

SUPPORTED_VIDEO_FORMATS = {"mp4", "mov", "mkv", "avi", "webm"}

# ─── Fonts ───────────────────────────────────────────────────────────────────
# Keys = display names shown to user
# Values = path to .ttf file inside bot/fonts/
FONTS = {
    "Montserrat Bold":   "bot/fonts/Montserrat-Bold.ttf",
    "Roboto Bold":       "bot/fonts/Roboto-Bold.ttf",
    "Open Sans Bold":    "bot/fonts/OpenSans-Bold.ttf",
    "Oswald Bold":       "bot/fonts/Oswald-Bold.ttf",
    "Bebas Neue":        "bot/fonts/BebasNeue-Regular.ttf",
    "Raleway Bold":      "bot/fonts/Raleway-Bold.ttf",
    "Playfair Bold":     "bot/fonts/PlayfairDisplay-Bold.ttf",
    "Lato Bold":         "bot/fonts/Lato-Bold.ttf",
    "Ubuntu Bold":       "bot/fonts/Ubuntu-Bold.ttf",
    "Roboto Condensed":  "bot/fonts/RobotoCondensed-Bold.ttf",
    "Arial":             "bot/fonts/Arial.ttf",
}

# ─── Sizes ───────────────────────────────────────────────────────────────────
# User-facing labels. Internally mapped to % of video width in ffmpeg_service.py
SIZES = ["10", "12", "14", "16", "18", "20", "24", "28", "32", "36", "48", "64"]

# ─── Opacity ─────────────────────────────────────────────────────────────────
# User-facing % values. Stored in DB as 0.0–1.0 float (divided by 100).
OPACITIES = ["10", "20", "30", "40", "50", "60", "70", "80", "90", "100"]

COLORS = ["white", "black", "red", "green", "blue", "yellow", "orange", "gray"]

POSITIONS = {
    "left_top":      "Лев.верх",
    "center_top":    "Центр верх",
    "right_top":     "Прав.верх",
    "left_center":   "Лев.центр",
    "center":        "Центр",
    "right_center":  "Прав.центр",
    "left_bottom":   "Лев.низ",
    "center_bottom": "Центр низ",
    "right_bottom":  "Прав.низ",
}

TELEGRAM_FILE_LIMIT = 50 * 1024 * 1024
TELEGRAM_DOCUMENT_LIMIT = 2 * 1024 * 1024 * 1024
