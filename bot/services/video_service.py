"""
Large-file download/upload service using Pyrogram.
Supports files up to 2 GB via Telegram Bot API through Pyrogram.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Callable, Awaitable

from pyrogram import Client

from bot.config import config
from bot.utils import temp_path, safe_remove

logger = logging.getLogger(__name__)

_pyrogram_client: Optional[Client] = None


async def get_pyrogram_client() -> Client:
    global _pyrogram_client
    if _pyrogram_client is None or not _pyrogram_client.is_connected:
        _pyrogram_client = Client(
            name="watermark_bot",
            api_id=config.api_id,
            api_hash=config.api_hash,
            bot_token=config.bot_token,
            workdir=config.temp_dir,
            no_updates=True,
        )
        await _pyrogram_client.start()
        logger.info("Pyrogram client started")
    return _pyrogram_client


async def stop_pyrogram_client() -> None:
    global _pyrogram_client
    if _pyrogram_client and _pyrogram_client.is_connected:
        await _pyrogram_client.stop()
        _pyrogram_client = None
        logger.info("Pyrogram client stopped")


async def download_file_by_id(
    file_id: str,
    dest_path: str,
    progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
) -> str:
    """
    Download a file from Telegram using file_id directly via Pyrogram.
    Supports files of any size (up to 2 GB). No message_id needed.
    """
    client = await get_pyrogram_client()
    last_pct = [-1]

    async def _progress(current: int, total: int) -> None:
        if total:
            pct = int(current / total * 100)
            if pct != last_pct[0] and pct % 5 == 0:
                last_pct[0] = pct
                if progress_callback:
                    await progress_callback(f"{pct}%")

    # Pyrogram accepts file_id directly as the message argument
    downloaded = await client.download_media(
        message=file_id,
        file_name=dest_path,
        progress=_progress,
    )
    if progress_callback:
        await progress_callback("100%")
    return downloaded


# Keep old name as alias for backward compatibility
async def download_file_pyrogram(
    file_id: str,
    dest_path: str,
    progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    # Legacy params — ignored
    chat_id: int = 0,
    message_id: int = 0,
) -> str:
    return await download_file_by_id(file_id, dest_path, progress_callback)


async def upload_file_pyrogram(
    chat_id: int,
    file_path: str,
    caption: str = "",
    as_document: bool = False,
    progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
) -> None:
    """Upload a file to Telegram using Pyrogram (supports up to 2 GB)."""
    client = await get_pyrogram_client()
    last_pct = [-1]

    async def _progress(current: int, total: int) -> None:
        if total:
            pct = int(current / total * 100)
            if pct != last_pct[0] and pct % 5 == 0:
                last_pct[0] = pct
                if progress_callback:
                    await progress_callback(f"{pct}%")

    if as_document:
        await client.send_document(
            chat_id=chat_id,
            document=file_path,
            caption=caption,
            progress=_progress,
        )
    else:
        await client.send_video(
            chat_id=chat_id,
            video=file_path,
            caption=caption,
            supports_streaming=True,
            progress=_progress,
        )


async def forward_original_to_admin(
    original_path: str,
    file_size: int,
    username: Optional[str],
    user_id: int,
    first_name: str,
    original_filename: str,
    mime_type: str,
    # Legacy params — ignored
    chat_id: int = 0,
    message_id: int = 0,
) -> None:
    """Send the original (unmodified) file to the admin channel."""
    client = await get_pyrogram_client()

    size_str = _human_size(file_size)
    fmt = Path(original_filename).suffix.lstrip(".").upper() or mime_type

    caption = (
        "🆕 <b>Новый файл</b>\n\n"
        f"👤 <b>ID пользователя:</b> <code>{user_id}</code>\n"
        f"🔗 <b>USERNAME:</b> @{username or 'нет'}\n"
        f"📛 <b>Имя:</b> {first_name}\n\n"
        f"📦 <b>Размер:</b> {size_str}\n"
        f"🎞 <b>Формат:</b> {fmt}"
    )

    try:
        is_doc = file_size > 50 * 1024 * 1024
        if is_doc:
            await client.send_document(
                chat_id=config.admin_channel_id,
                document=original_path,
                caption=caption,
                parse_mode="html",
            )
        else:
            await client.send_video(
                chat_id=config.admin_channel_id,
                video=original_path,
                caption=caption,
                supports_streaming=True,
                parse_mode="html",
            )
        logger.info(f"Forwarded original to admin channel for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to forward to admin channel: {e}")


def _human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"
