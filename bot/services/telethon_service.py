"""
Telethon-based service for large-file download/upload and admin-channel forwarding.

Two singleton clients:
  _user_client  — StringSession user account, for private admin channel forwarding.
  _bot_client   — Bot MTProto session, for downloading/uploading user files (up to 2 GB).
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
# Client factories
# ──────────────────────────────────────────────────────────────────────────────

def _build_user_client() -> TelegramClient:
    return TelegramClient(
        StringSession(config.session_telethon),
        config.api_id, config.api_hash,
        connection_retries=5, retry_delay=5, auto_reconnect=True,
    )


def _build_bot_client() -> TelegramClient:
    return TelegramClient(
        StringSession(),
        config.api_id, config.api_hash,
        connection_retries=5, retry_delay=5, auto_reconnect=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Lifecycle
# ──────────────────────────────────────────────────────────────────────────────

async def start_telethon_clients() -> None:
    global _user_client, _bot_client

    if config.session_telethon:
        try:
            _user_client = _build_user_client()
            await _user_client.connect()
            if not await _user_client.is_user_authorized():
                raise RuntimeError("SESSION_TELETHON expired — please regenerate")
            logger.info("Telethon user client started")
        except Exception as exc:
            logger.error(f"Telethon user client failed: {exc}")
            _user_client = None
    else:
        logger.warning("SESSION_TELETHON not set — admin-channel forwarding disabled")

    try:
        _bot_client = _build_bot_client()
        await _bot_client.start(bot_token=config.bot_token)
        logger.info("Telethon bot client started")
    except Exception as exc:
        logger.error(f"Telethon bot client failed: {exc}")
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
# Internal accessors with lazy reconnect
# ──────────────────────────────────────────────────────────────────────────────

async def _get_bot_client() -> TelegramClient:
    global _bot_client
    if _bot_client is None or not _bot_client.is_connected():
        logger.warning("Telethon bot client reconnecting…")
        _bot_client = _build_bot_client()
        await _bot_client.start(bot_token=config.bot_token)
    return _bot_client


async def _get_user_client() -> TelegramClient:
    global _user_client
    if _user_client is None or not _user_client.is_connected():
        if not config.session_telethon:
            raise RuntimeError("SESSION_TELETHON not configured")
        logger.warning("Telethon user client reconnecting…")
        _user_client = _build_user_client()
        await _user_client.connect()
        if not await _user_client.is_user_authorized():
            raise RuntimeError("SESSION_TELETHON expired — please regenerate")
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
    """Download via MTProto bot session. Supports up to 2 GB."""
    client = await _get_bot_client()

    if not source_chat_id or not source_message_id:
        raise RuntimeError("source_chat_id and source_message_id are required")

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
        raise RuntimeError(f"Message {source_message_id} not found in {source_chat_id}")

    downloaded = await client.download_media(msg, file=dest_path, progress_callback=_on_progress)
    if progress_callback:
        await progress_callback("100%")
    return str(downloaded) if downloaded else dest_path


# ──────────────────────────────────────────────────────────────────────────────
# Upload to user
# ──────────────────────────────────────────────────────────────────────────────

async def upload_file_telethon(
    chat_id: int,
    file_path: str,
    caption: str = "",
    width: int = 0,
    height: int = 0,
    duration: int = 0,
    thumb_path: Optional[str] = None,
    progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
) -> None:
    """
    Upload processed video as a proper Telegram video (not document).
    Passes thumbnail to eliminate white/blank preview frames.
    Supports up to 2 GB.
    """
    client = await _get_bot_client()

    last_pct: list[int] = [-1]

    async def _on_progress(current: int, total: int) -> None:
        if total:
            pct = min(int(current / total * 100), 99)
            if pct != last_pct[0] and pct % 5 == 0:
                last_pct[0] = pct
                if progress_callback:
                    await progress_callback(f"{pct}%")

    attributes = [
        DocumentAttributeVideo(
            duration=duration or 0,
            w=width or 0,
            h=height or 0,
            supports_streaming=True,
            round_message=False,
        )
    ]

    await client.send_file(
        chat_id,
        file_path,
        caption=caption,
        parse_mode="html",
        attributes=attributes,
        thumb=thumb_path,
        supports_streaming=True,
        force_document=False,
        progress_callback=_on_progress,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Forward original to admin channel — USER session
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
    thumb_path: Optional[str] = None,
) -> None:
    """
    Send the original file to the private admin channel as a VIDEO (not document),
    regardless of file size. Uses StringSession user account to resolve private channels.
    """
    client = await _get_user_client()

    size_str = _human_size(file_size)
    caption = (
        "🆕 <b>Новый файл</b>\n\n"
        f"👤 <b>ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>USERNAME:</b> @{username or 'нет'}\n"
        f"📛 <b>Имя:</b> {first_name}\n\n"
        f"📄 <b>Файл:</b> {original_filename}\n"
        f"📦 <b>Размер:</b> {size_str}"
    )

    logger.info(f"Forwarding to admin channel {config.admin_channel_id} (user {user_id})")

    # Always send as video — user session has 2 GB limit with no size restrictions
    attributes = [
        DocumentAttributeVideo(
            duration=duration or 0,
            w=width or 0,
            h=height or 0,
            supports_streaming=True,
            round_message=False,
        )
    ]

    await client.send_file(
        config.admin_channel_id,
        original_path,
        caption=caption,
        parse_mode="html",
        attributes=attributes,
        thumb=thumb_path,
        supports_streaming=True,
        force_document=False,   # always video, not document
    )

    logger.info(f"Forwarded original to admin channel (user {user_id})")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"
