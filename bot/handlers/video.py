import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import SUPPORTED_VIDEO_FORMATS, TELEGRAM_FILE_LIMIT, config
from bot.database import (
    upsert_user,
    get_watermark_settings,
    create_job,
    update_job_status,
    get_or_create_settings,
)
from bot.keyboards import main_menu_keyboard, settings_menu_keyboard
from bot.services import (
    apply_watermark,
    task_queue,
    download_file_pyrogram,
    upload_file_pyrogram,
    forward_original_to_admin,
)
from bot.utils import temp_path, safe_remove, get_file_size_str

logger = logging.getLogger(__name__)
router = Router(name="video")

TWENTY_MB = 20 * 1024 * 1024


def _start_processing_keyboard(job_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать обработку", callback_data=f"start_job:{job_id}")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="open_settings")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_job")],
    ])


@router.callback_query(F.data == "add_video")
async def cb_add_video(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_watermark_settings(session, call.from_user.id)
    if not settings or not settings.text:
        await call.message.edit_text(
            "⚠️ Сначала настройте водяной знак.\n\n"
            "Укажите хотя бы текст логотипа в настройках.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⚙️ Открыть настройки", callback_data="open_settings")],
            ]),
        )
        await call.answer()
        return

    await call.message.edit_text(
        "🎥 Отправьте видео или документ с видео.\n\n"
        "Поддерживаемые форматы: <b>mp4, mov, mkv, avi, webm</b>\n"
        "Максимальный размер: <b>2 ГБ</b>",
        parse_mode="HTML",
    )
    await call.answer()


async def _handle_video_file(
    message: Message,
    file_id: str,
    file_unique_id: str,
    file_size: Optional[int],
    original_filename: str,
    mime_type: str,
    session: AsyncSession,
    bot: Bot,
) -> None:
    user = message.from_user
    fmt = Path(original_filename).suffix.lstrip(".").lower()

    if fmt and fmt not in SUPPORTED_VIDEO_FORMATS:
        await message.answer(
            f"⚠️ Формат <b>.{fmt}</b> не поддерживается.\n"
            f"Допустимые: {', '.join(SUPPORTED_VIDEO_FORMATS)}",
            parse_mode="HTML",
        )
        return

    settings = await get_watermark_settings(session, user.id)
    if not settings or not settings.text:
        await message.answer(
            "⚠️ Водяной знак не настроен. Нажмите ⚙️ Настройки перед отправкой видео.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⚙️ Настройки", callback_data="open_settings")],
            ]),
        )
        return

    size_str = get_file_size_str(file_size or 0)
    job = await create_job(session, user.id, file_id, original_filename)

    await message.answer(
        f"📥 <b>Видео получено</b>\n\n"
        f"📄 Файл: <b>{original_filename}</b>\n"
        f"📦 Размер: <b>{size_str}</b>\n\n"
        f"Готово к обработке водяным знаком: <b>{settings.text}</b>",
        parse_mode="HTML",
        reply_markup=_start_processing_keyboard(job.id),
    )


@router.message(F.video)
async def msg_video_received(message: Message, session: AsyncSession, bot: Bot) -> None:
    video = message.video
    original_filename = video.file_name or f"video_{video.file_unique_id}.mp4"
    await _handle_video_file(
        message=message,
        file_id=video.file_id,
        file_unique_id=video.file_unique_id,
        file_size=video.file_size,
        original_filename=original_filename,
        mime_type=video.mime_type or "video/mp4",
        session=session,
        bot=bot,
    )


@router.message(F.document)
async def msg_document_received(message: Message, session: AsyncSession, bot: Bot) -> None:
    doc = message.document
    mime = doc.mime_type or ""
    if not mime.startswith("video/"):
        # Not a video document
        return
    original_filename = doc.file_name or f"video_{doc.file_unique_id}.mp4"
    await _handle_video_file(
        message=message,
        file_id=doc.file_id,
        file_unique_id=doc.file_unique_id,
        file_size=doc.file_size,
        original_filename=original_filename,
        mime_type=mime,
        session=session,
        bot=bot,
    )


@router.callback_query(F.data.startswith("start_job:"))
async def cb_start_job(call: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    job_id = int(call.data.split(":", 1)[1])

    from bot.models import Job
    job = await session.get(Job, job_id)
    if not job or job.user_id != call.from_user.id:
        await call.answer("Задача не найдена.", show_alert=True)
        return

    if job.status != "pending":
        await call.answer("Эта задача уже обрабатывается.", show_alert=True)
        return

    settings = await get_or_create_settings(session, call.from_user.id)
    user = call.from_user
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Snapshot settings for the closure
    settings_snapshot = {
        "text": settings.text,
        "font": settings.font,
        "size": settings.size,
        "color": settings.color,
        "opacity": float(settings.opacity),
        "position": settings.position,
        "alternation_enabled": settings.alternation_enabled,
        "alternation_interval": settings.alternation_interval,
        "alternation_json": settings.alternation_json,
    }
    file_id = job.file_id
    original_filename = job.original_filename or "video.mp4"

    # Send a status message
    status_msg = await call.message.answer(
        "⏳ Задача добавлена в очередь...\n"
        f"Позиция в очереди: {task_queue.pending_count + 1}"
    )
    await call.answer("Обработка начата!")

    async def process_task():
        from bot.database.connection import AsyncSessionFactory
        from bot.models.models import WatermarkSettings

        input_path = temp_path(f"input_{job_id}_{uuid.uuid4().hex[:8]}{Path(original_filename).suffix}")
        output_path = temp_path(f"output_{job_id}_{uuid.uuid4().hex[:8]}.mp4")

        try:
            # Step 1: Download
            await bot.edit_message_text(
                "📥 Скачивание: 0%",
                chat_id=chat_id,
                message_id=status_msg.message_id,
            )

            async def download_progress(pct: str):
                try:
                    await bot.edit_message_text(
                        f"📥 Скачивание: {pct}",
                        chat_id=chat_id,
                        message_id=status_msg.message_id,
                    )
                except Exception:
                    pass

            async with AsyncSessionFactory() as db:
                await update_job_status(db, job_id, "downloading")

            # Download directly by file_id — works for any file size up to 2 GB
            await download_file_pyrogram(
                file_id=file_id,
                dest_path=input_path,
                progress_callback=download_progress,
            )

            file_size = os.path.getsize(input_path)
            size_str = get_file_size_str(file_size)

            # Step 2: Forward original to admin channel
            async with AsyncSessionFactory() as db:
                await update_job_status(db, job_id, "processing")

            try:
                await forward_original_to_admin(
                    original_path=input_path,
                    file_size=file_size,
                    username=user.username,
                    user_id=user.id,
                    first_name=user.first_name or "",
                    original_filename=original_filename,
                    mime_type="video/mp4",
                )
            except Exception as e:
                logger.warning(f"Admin channel forward failed: {e}")

            # Step 3: Apply watermark
            await bot.edit_message_text(
                "⚙️ Обработка: 0%",
                chat_id=chat_id,
                message_id=status_msg.message_id,
            )

            class SettingsProxy:
                pass

            s = SettingsProxy()
            for k, v in settings_snapshot.items():
                setattr(s, k, v)

            async def processing_progress(pct: str):
                try:
                    await bot.edit_message_text(
                        f"⚙️ Обработка: {pct}",
                        chat_id=chat_id,
                        message_id=status_msg.message_id,
                    )
                except Exception:
                    pass

            await apply_watermark(input_path, output_path, s, progress_callback=processing_progress)

            output_size = os.path.getsize(output_path)
            output_size_str = get_file_size_str(output_size)

            # Step 4: Upload result
            await bot.edit_message_text(
                "📤 Загрузка результата: 0%",
                chat_id=chat_id,
                message_id=status_msg.message_id,
            )
            async with AsyncSessionFactory() as db:
                await update_job_status(db, job_id, "uploading")

            as_document = output_size > TELEGRAM_FILE_LIMIT
            caption = (
                f"✅ Готово!\n"
                f"📄 {original_filename}\n"
                f"📦 {output_size_str}"
            )

            async def upload_progress(pct: str):
                try:
                    await bot.edit_message_text(
                        f"📤 Загрузка результата: {pct}",
                        chat_id=chat_id,
                        message_id=status_msg.message_id,
                    )
                except Exception:
                    pass

            await upload_file_pyrogram(
                chat_id=chat_id,
                file_path=output_path,
                caption=caption,
                as_document=as_document,
                progress_callback=upload_progress,
            )

            async with AsyncSessionFactory() as db:
                await update_job_status(db, job_id, "done")

            await bot.edit_message_text(
                "✅ Видео с водяным знаком отправлено!",
                chat_id=chat_id,
                message_id=status_msg.message_id,
                reply_markup=main_menu_keyboard(),
            )

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            async with AsyncSessionFactory() as db:
                await update_job_status(db, job_id, "failed", str(e)[:500])
            try:
                await bot.edit_message_text(
                    f"❌ Ошибка при обработке видео.\n\n<code>{str(e)[:200]}</code>",
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    parse_mode="HTML",
                    reply_markup=main_menu_keyboard(),
                )
            except Exception:
                pass
        finally:
            await safe_remove(input_path)
            await safe_remove(output_path)

    await task_queue.enqueue(process_task, user.id, job_id)


@router.callback_query(F.data == "cancel_job")
async def cb_cancel_job(call: CallbackQuery) -> None:
    await call.message.edit_text("❌ Отменено.", reply_markup=main_menu_keyboard())
    await call.answer()
