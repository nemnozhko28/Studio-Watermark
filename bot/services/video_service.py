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
    client = await get_pyrogram_client()
    last_pct = [-1]

    async def _progress(current: int, total: int) -> None:
        if total:
            pct = int(current / total * 100)
            if pct != last_pct[0] and pct % 5 == 0:
                last_pct[0] = pct
                if progress_callback:
                    await progress_callback(f"{pct}%")

    downloaded = await client.download_media(
        message=file_id,
        file_name=dest_path,
        progress=_progress,
    )
    if progress_callback:
        await progress_callback("100%")
    return downloaded


async def download_file_pyrogram(
    file_id: str,
    dest_path: str,
    progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    chat_id: int = 0,
    message_id: int = 0,
) -> str:
    return await download_file_by_id(file_id, dest_path, progress_callback)


async def upload_file_pyrogram(
    chat_id: int,
    file_path: str,
    caption: str = "",
    as_document: bool = False,
    width: int = 0,
    height: int = 0,
    duration: int = 0,
    progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
) -> None:
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
            width=width or None,
            height=height or None,
            duration=duration or None,
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
    width: int = 0,
    height: int = 0,
    duration: int = 0,
) -> None:
    """Send original to admin channel using aiogram with FSInputFile"""
    from aiogram import Bot
    from aiogram.enums import ParseMode
    from aiogram.types import FSInputFile

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

    admin_channel = config.admin_channel_id
    logger.info(f"Forwarding original to admin channel {admin_channel} via aiogram")

    bot = None
    try:
        bot = Bot(token=config.bot_token)
        video_file = FSInputFile(original_path)

        is_doc = file_size > 50 * 1024 * 1024

        if is_doc:
            await bot.send_document(
                chat_id=admin_channel,
                document=video_file,
                caption=caption,
                parse_mode=ParseMode.HTML,
            )
        else:
            await bot.send_video(
                chat_id=admin_channel,
                video=video_file,
                caption=caption,
                supports_streaming=True,
                width=width or None,
                height=height or None,
                duration=duration or None,
                parse_mode=ParseMode.HTML,
            )

        logger.info(f"✅ Successfully forwarded original to admin channel via aiogram")

    except Exception as e:
        logger.error(f"Admin channel forward failed: {e}", exc_info=True)
        try:
            if bot:
                await bot.send_message(
                    config.admin_id,
                    f"⚠️ Ошибка отправки в канал:\n<code>{str(e)[:400]}</code>\n\n"
                    f"Channel ID: <code>{admin_channel}</code>",
                    parse_mode=ParseMode.HTML,
                )
        except:
            pass
    finally:
        if bot:
            try:
                await bot.session.close()
            except:
                pass


def _human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"
