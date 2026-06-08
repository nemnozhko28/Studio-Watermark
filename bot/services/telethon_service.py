"""
Telethon-based service for large-file download/upload and admin-channel forwarding.

Two singleton clients:
  _user_client  — StringSession user account, used ONLY for forwarding to the
                  private admin channel (resolves private peers that bot sessions
                  cannot reach).
  _bot_client   — Bot session (bot_token via MTProto), used for downloading files
                  sent to the bot and uploading processed results back to users.
                  Supports files up to 2 GB.
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Callable, Awaitable

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeVideo

from bot.config import config

logger = logging.getLogger(__name__)

_user_client: Optional[TelegramClient] = None
_bot_client: Optional[TelegramClient] = None


# ──────────────────────────────────────────────────────────────────────────────
# Client factory helpers
# ──────────────────────────────────────────────────────────────────────────────

def _build_user_client() -> TelegramClient:
    return TelegramClient(
        StringSession(config.session_telethon),
        config.api_id,
        config.api_hash,
        connection_retries=5,
        retry_delay=5,
        auto_reconnect=True,
    )


def _build_bot_client() -> TelegramClient:
    return TelegramClient(
        StringSession(),
        config.api_id,
        config.api_hash,
        connection_retries=5,
        retry_delay=5,
        auto_reconnect=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Lifecycle — call from main.py on startup / shutdown
# ──────────────────────────────────────────────────────────────────────────────

async def start_telethon_clients() -> None:
    global _user_client, _bot_client

    if config.session_telethon:
        try:
            _user_client = _build_user_client()
            await _user_client.connect()
            if not await _user_client.is_user_authorized():
                raise RuntimeError(
                    "SESSION_TELETHON is expired or invalid — please regenerate it"
                )
            logger.info("Telethon user client started")
        except Exception as exc:
            logger.error(f"Telethon user client failed to start: {exc}")
            _user_client = None
    else:
        logger.warning(
            "SESSION_TELETHON is not set — admin-channel forwarding will be disabled"
        )

    try:
        _bot_client = _build_bot_client()
        await _bot_client.start(bot_token=config.bot_token)
        logger.info("Telethon bot client started")
    except Exception as exc:
        logger.error(f"Telethon bot client failed to start: {exc}")
        _bot_client = None


async def stop_telethon_clients() -> None:
    global _user_client, _bot_client
    if _bot_client and _bot_client.is_connected():
        await _bot_client.disconnect()
        _bot_client = None
        logger.info("Telethon bot client stopped")
    if _user_client and _user_client.is_connected():
        await _user_client.disconnect()
        _user_client = None
        logger.info("Telethon user client stopped")


# ──────────────────────────────────────────────────────────────────────────────
# Internal — safe accessors with lazy reconnect
# ──────────────────────────────────────────────────────────────────────────────

async def _get_bot_client() -> TelegramClient:
    global _bot_client
    if _bot_client is None or not _bot_client.is_connected():
        logger.warning("Telethon bot client disconnected — reconnecting…")
        _bot_client = _build_bot_client()
        await _bot_client.start(bot_token=config.bot_token)
        logger.info("Telethon bot client reconnected")
    return _bot_client


async def _get_user_client() -> TelegramClient:
    global _user_client
    if _user_client is None or not _user_client.is_connected():
        if not config.session_telethon:
            raise RuntimeError(
                "SESSION_TELETHON is not configured — cannot send to admin channel"
            )
        logger.warning("Telethon user client disconnected — reconnecting…")
        _user_client = _build_user_client()
        await _user_client.connect()
        if not await _user_client.is_user_authorized():
            raise RuntimeError("SESSION_TELETHON is expired — please regenerate it")
        logger.info("Telethon user client reconnected")
    return _user_client


# ──────────────────────────────────────────────────────────────────────────────
# Download
# ──────────────────────────────────────────────────────────────────────────────

async def download_file_telethon(
    file_id: str,
    dest_path: str,
    progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    source_chat_id: int = 0,
    source_message_id: int = 0,
) -> str:
    """
    Download a Telegram file via MTProto (bot session). Supports up to 2 GB.

    source_chat_id + source_message_id are required — they let Telethon fetch the
    actual Message object so it can locate the file on Telegram's DC.
    """
    client = await _get_bot_client()

    if not source_chat_id or not source_message_id:
        raise RuntimeError(
            "source_chat_id and source_message_id are required for Telethon download"
        )

    last_pct: list[int] = [-1]

    async def _on_progress(current: int, total: int) -> None:
        if total:
            pct = min(int(current / total * 100), 99)
            if pct != last_pct[0] and pct % 5 == 0:
                last_pct[0] = pct
                if progress_callback:
                    await progress_callback(f"{pct}%")

    msg = await client.get_messages(source_chat_id, ids=source_message_id)
    if msg is None:
        raise RuntimeError(
            f"Message {source_message_id} not found in chat {source_chat_id}"
        )

    downloaded = await client.download_media(
        msg,
        file=dest_path,
        progress_callback=_on_progress,
    )

    if progress_callback:
        await progress_callback("100%")

    return str(downloaded) if downloaded else dest_path


# ──────────────────────────────────────────────────────────────────────────────
# Upload to user chat
# ──────────────────────────────────────────────────────────────────────────────

async def upload_file_telethon(
    chat_id: int,
    file_path: str,
    caption: str = "",
    as_document: bool = False,
    width: int = 0,
    height: int = 0,
    duration: int = 0,
    progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
) -> None:
    """Upload a processed video to a Telegram chat using the bot session. Supports up to 2 GB."""
    client = await _get_bot_client()

    last_pct: list[int] = [-1]

    async def _on_progress(current: int, total: int) -> None:
        if total:
            pct = min(int(current / total * 100), 99)
            if pct != last_pct[0] and pct % 5 == 0:
                last_pct[0] = pct
                if progress_callback:
                    await progress_callback(f"{pct}%")

    attributes = []
    if not as_document and (width or height or duration):
        attributes.append(
            DocumentAttributeVideo(
                duration=duration or 0,
                w=width or 0,
                h=height or 0,
                supports_streaming=True,
                round_message=False,
            )
        )

    await client.send_file(
        chat_id,
        file_path,
        caption=caption,
        parse_mode="html",
        force_document=as_document,
        attributes=attributes if attributes else None,
        supports_streaming=(not as_document),
        progress_callback=_on_progress,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Forward original to admin channel (USER session)
# ──────────────────────────────────────────────────────────────────────────────

async def forward_original_to_admin(
    original_path: str,
    file_size: int,
    username: Optional[str],
    user_id: int,
    first_name: str,
    original_filename: str,
    mime_type: str,
    width: int = 0,
    height: int = 0,
    duration: int = 0,
) -> None:
    """
    Send the unmodified original file to the private admin channel.

    Uses the Telethon USER session (StringSession) which can resolve private
    channel peers that bot sessions cannot — this was the root cause of the
    'Peer id invalid / ID not found' errors with Pyrogram.

    Errors are logged but never re-raised so the main processing pipeline
    always continues and the user always receives their watermarked result.
    """
    client = await _get_user_client()

    size_str = _human_size(file_size)
    fmt = Path(original_filename).suffix.lstrip(".").upper() or mime_type

    caption = (
        "🆕 <b>Новый файл</b>\n\n"
        f"👤 <b>ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>USERNAME:</b> @{username or 'нет'}\n"
        f"📛 <b>Имя:</b> {first_name}\n\n"
        f"📄 <b>Файл:</b> {original_filename}\n"
        f"📦 <b>Размер:</b> {size_str}"
    )

    admin_channel = config.admin_channel_id
    logger.info(
        f"Forwarding original to admin channel {admin_channel} for user {user_id}"
    )

    is_doc = file_size > 50 * 1024 * 1024

    attributes = []
    if not is_doc and (width or height or duration):
        attributes.append(
            DocumentAttributeVideo(
                duration=duration or 0,
                w=width or 0,
                h=height or 0,
                supports_streaming=True,
                round_message=False,
            )
        )

    await client.send_file(
        admin_channel,
        original_path,
        caption=caption,
        parse_mode="html",
        force_document=is_doc,
        attributes=attributes if attributes else None,
        supports_streaming=(not is_doc),
    )

    logger.info(
        f"Forwarded original to admin channel successfully for user {user_id}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"
