# Pyrogram → Telethon Migration Notes

## New ENV variables

| Variable | Required | Description |
|---|---|---|
| `SESSION_TELETHON` | Yes (for admin channel) | Telethon StringSession string for the user account that is a member of `ADMIN_CHANNEL_ID` |
| `API_ID` | Yes | Same as before |
| `API_HASH` | Yes | Same as before |

`BOT_TOKEN`, `ADMIN_ID`, `ADMIN_CHANNEL_ID`, `DATABASE_URL`, `MAX_WORKERS` — unchanged.

---

## How to generate SESSION_TELETHON

Run **once** locally (not on Railway):

```bash
pip install telethon
python3 - <<'EOF'
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os

API_ID = int(input("API_ID: "))
API_HASH = input("API_HASH: ")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\nYour SESSION_TELETHON string:\n")
    print(client.session.save())
EOF
```

Paste the printed string into Railway → Variables → `SESSION_TELETHON`.

The account used **must be a member or admin** of the private `ADMIN_CHANNEL_ID` channel.

---

## Database migration (existing deployments)

The `jobs` table has two new nullable columns:

```sql
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_chat_id BIGINT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_message_id BIGINT;
```

Fresh deployments (new DB) need no manual migration — `init_db()` runs
`create_all` which creates the columns automatically.

**Railway**: run the SQL above in your Railway Postgres console, or wipe the DB
and let the bot recreate the schema on next startup.

---

## Removed

| What | Where it was |
|---|---|
| `pyrogram` | `requirements.txt` |
| `tgcrypto` | `requirements.txt` |
| `get_pyrogram_client()` | `bot/services/video_service.py` (entire file replaced) |
| `stop_pyrogram_client()` | same |
| `download_file_pyrogram()` | same |
| `upload_file_pyrogram()` | same |
| `pyrogram.Client(bot_token=...)` | `bot/main.py` startup |

---

## Changed files summary

| File | Change |
|---|---|
| `bot/services/telethon_service.py` | **NEW** — replaces `video_service.py` |
| `bot/services/__init__.py` | Updated exports (Telethon names) |
| `bot/main.py` | `start/stop_telethon_clients` instead of Pyrogram |
| `bot/config.py` | Added `session_telethon` field |
| `bot/models/models.py` | Added `source_chat_id`, `source_message_id` to `Job` |
| `bot/database/queries.py` | `create_job` accepts the two new fields |
| `bot/handlers/video.py` | Passes `source_chat_id/message_id`; uses Telethon service |
| `requirements.txt` | `pyrogram` + `tgcrypto` removed; `telethon==1.36.0` added |
| `.env.example` | Added `SESSION_TELETHON` |
