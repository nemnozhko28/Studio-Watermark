# Migration Notes

## New ENV variables

| Variable | Required | Description |
|---|---|---|
| `SESSION_TELETHON` | Yes (for admin channel) | Telethon StringSession for the user account that is a member of `ADMIN_CHANNEL_ID` |
| `API_ID` | Yes | Telegram API ID |
| `API_HASH` | Yes | Telegram API hash |

`BOT_TOKEN`, `ADMIN_ID`, `ADMIN_CHANNEL_ID`, `DATABASE_URL`, `MAX_WORKERS` — unchanged.

---

## How to generate SESSION_TELETHON

Run **once** locally (not on Railway):

```bash
pip install telethon
python3 - <<'EOF'
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = int(input("API_ID: "))
API_HASH = input("API_HASH: ")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\nYour SESSION_TELETHON:\n")
    print(client.session.save())
EOF
```

Paste the string into Railway → Variables → `SESSION_TELETHON`.  
The account **must be a member or admin** of `ADMIN_CHANNEL_ID`.

---

## Database migration (existing deployments)

Run these SQL commands in your Railway Postgres console:

```sql
-- v1 → v2: Telethon migration
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_chat_id BIGINT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_message_id BIGINT;

-- v2 → v3: English language support
ALTER TABLE watermark_settings ADD COLUMN IF NOT EXISTS language VARCHAR(5) DEFAULT 'ru';
```

Fresh deployments (new DB) need **no manual migration** — `init_db()` runs `create_all` automatically.

---

## What changed in v3 (English language)

| File | Change |
|---|---|
| `bot/i18n.py` | **NEW** — all UI strings in Russian + English |
| `bot/models/models.py` | Added `language` field to `WatermarkSettings` |
| `bot/database/queries.py` | Added `update_language()`, `get_lang()` |
| `bot/database/__init__.py` | Exported `update_language` |
| `bot/keyboards/main_kb.py` | **NEW** — accepts `lang` param |
| `bot/keyboards/position_kb.py` | **NEW** — accepts `lang` param |
| `bot/keyboards/settings_kb.py` | Added language button, `lang` param |
| `bot/keyboards/__init__.py` | Exported `language_keyboard` |
| `bot/handlers/start.py` | **NEW** — uses i18n for all messages |
| `bot/handlers/settings.py` | Uses i18n + new language selection handler |
| `bot/handlers/video.py` | Uses i18n for all messages |
| `bot/handlers/__init__.py` | **NEW** — registers routers |

## What changed in v2 (7 UX fixes)

| Fix | What changed |
|---|---|
| Admin sends as video | `force_document=False` always in `telethon_service.py` |
| White thumbnail | `generate_thumbnail()` in `ffmpeg_service.py`, passed as `thumb=` |
| Menu after done | `bot.send_message(main_menu_keyboard)` after upload in `video.py` |
| More fonts | 11 fonts in `config.py` + `download_fonts.sh` |
| Friendly sizes | `10,12,14…64` labels → mapped to `%` of width in `ffmpeg_service.py` |
| Opacity as % | `10%–100%` in UI, stored as `0.0–1.0` in DB |
| Speed | `-preset ultrafast -threads 0` in FFmpeg |
