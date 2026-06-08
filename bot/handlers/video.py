import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import SUPPORTED_VIDEO_FORMATS, config
from bot.database import (
    upsert_user,
    get_watermark_settings,
    create_job,
    update_job_status,
    get_or_create_settings,
)
from bot.database.queries import get_lang
from bot.keyboards import main_menu_keyboard, settings_menu_keyboard
from bot.services import (
    apply_watermark,
    get_video_info,
    task_queue,
    download_file_telethon,
    upload_file_telethon,
    forward_original_to_admin,
)
from bot.services.ffmpeg_service import generate_thumbnail
from bot.utils import temp_path, safe_remove, get_file_size_str
from bot.i18n import t

logger = logging.getLogger(__name__)
router = Router(name="video")


def _start_processing_keyboard(job_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_start_proc", lang), callback_data=f"start_job:{job_id}")],
        [InlineKeyboardButton(text=t("btn_settings", lang),   callback_data="open_settings")],
        [InlineKeyboardButton(text=t("btn_cancel", lang),     callback_data="cancel_job")],
    ])


@router.callback_query(F.data == "add_video")
async def cb_add_video(call: CallbackQuery, session: AsyncSession) -> None:
    settings = await get_watermark_settings(session, call.from_user.id)
    lang = get_lang(settings) if settings else "ru"
    if not settings or not settings.text:
        await call.message.edit_text(
            t("no_text_warning", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("btn_open_settings", lang), callback_data="open_settings")],
            ]),
        )
        await call.answer()
        return
    await call.message.edit_text(t("send_video", lang), parse_mode="HTML")
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
    settings = await get_watermark_settings(session, user.id)
    lang = get_lang(settings) if settings else "ru"
    fmt = Path(original_filename).suffix.lstrip(".").lower()

    if fmt and fmt not in SUPPORTED_VIDEO_FORMATS:
        await message.answer(
            t("unsupported_format", lang, fmt=fmt, fmts=", ".join(SUPPORTED_VIDEO_FORMATS)),
            parse_mode="HTML",
        )
        return

    if not settings or not settings.text:
        await message.answer(
            t("no_settings", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("btn_open_settings", lang), callback_data="open_settings")],
            ]),
        )
        return

    size_str = get_file_size_str(file_size or 0)
    job = await create_job(
        session, user.id, file_id, original_filename,
        source_chat_id=message.chat.id,
        source_message_id=message.message_id,
    )

    await message.answer(
        t("video_received", lang, name=original_filename, size=size_str, wm=settings.text),
        parse_mode="HTML",
        reply_markup=_start_processing_keyboard(job.id, lang),
    )


@router.message(F.video)
async def msg_video_received(message: Message, session: AsyncSession, bot: Bot) -> None:
    video = message.video
    original_filename = video.file_name or f"video_{video.file_unique_id}.mp4"
    await _handle_video_file(
        message=message, file_id=video.file_id, file_unique_id=video.file_unique_id,
        file_size=video.file_size, original_filename=original_filename,
        mime_type=video.mime_type or "video/mp4", session=session, bot=bot,
    )


@router.message(F.document)
async def msg_document_received(message: Message, session: AsyncSession, bot: Bot) -> None:
    doc = message.document
    mime = doc.mime_type or ""
    if not mime.startswith("video/"):
        return
    original_filename = doc.file_name or f"video_{doc.file_unique_id}.mp4"
    await _handle_video_file(
        message=message, file_id=doc.file_id, file_unique_id=doc.file_unique_id,
        file_size=doc.file_size, original_filename=original_filename,
        mime_type=mime, session=session, bot=bot,
    )


@router.callback_query(F.data.startswith("start_job:"))
async def cb_start_job(call: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    job_id = int(call.data.split(":", 1)[1])

    from bot.models import Job
    job = await session.get(Job, job_id)
    if not job or job.user_id != call.from_user.id:
        await call.answer("Not found." if True else "Не найдено.", show_alert=True)
        return
    if job.status != "pending":
        await call.answer("Already processing." if True else "Уже обрабатывается.", show_alert=True)
        return

    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    user = call.from_user
    chat_id = call.message.chat.id

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
        "delay_seconds": getattr(settings, "delay_seconds", 0),
    }

    file_id = job.file_id
    original_filename = job.original_filename or "video.mp4"
    source_chat_id = job.source_chat_id or 0
    source_message_id = job.source_message_id or 0

    status_msg = await call.message.answer(
        t("queued", lang, n=task_queue.pending_count + 1)
    )
    await call.answer()

    async def process_task() -> None:
        from bot.database.connection import AsyncSessionFactory

        ext = Path(original_filename).suffix or ".mp4"
        uid = uuid.uuid4().hex[:8]
        input_path   = temp_path(f"input_{job_id}_{uid}{ext}")
        output_path  = temp_path(f"output_{job_id}_{uid}.mp4")
        thumb_path   = temp_path(f"thumb_{job_id}_{uid}.jpg")
        out_thumb_path = temp_path(f"out_thumb_{job_id}_{uid}.jpg")

        try:
            # ── 1. Download ──────────────────────────────────────────────────
            await bot.edit_message_text(
                t("downloading", lang, pct="0%"), chat_id=chat_id,
                message_id=status_msg.message_id,
            )

            async def dl_progress(pct: str) -> None:
                try:
                    await bot.edit_message_text(
                        t("downloading", lang, pct=pct), chat_id=chat_id,
                        message_id=status_msg.message_id,
                    )
                except Exception:
                    pass

            async with AsyncSessionFactory() as db:
                await update_job_status(db, job_id, "downloading")

            await download_file_telethon(
                file_id=file_id, dest_path=input_path,
                progress_callback=dl_progress,
                source_chat_id=source_chat_id,
                source_message_id=source_message_id,
            )

            file_size = os.path.getsize(input_path)
            vid_width = vid_height = vid_duration = 0
            try:
                info = await get_video_info(input_path)
                vid_width    = info.get("width", 0)
                vid_height   = info.get("height", 0)
                vid_duration = int(info.get("duration", 0))
            except Exception as exc:
                logger.warning(f"Could not get video info: {exc}")

            # Generate thumbnail from original for admin channel
            thumb = await generate_thumbnail(input_path, thumb_path)

            # ── 2. Forward original to admin channel ─────────────────────────
            async with AsyncSessionFactory() as db:
                await update_job_status(db, job_id, "processing")

            try:
                await forward_original_to_admin(
                    original_path=input_path, file_size=file_size,
                    username=user.username, user_id=user.id,
                    first_name=user.first_name or "",
                    original_filename=original_filename, mime_type="video/mp4",
                    width=vid_width, height=vid_height, duration=vid_duration,
                    thumb_path=thumb,
                )
            except Exception as exc:
                logger.error(f"Admin channel forward failed (job {job_id}): {exc}", exc_info=True)
                try:
                    await bot.send_message(
                        config.admin_id,
                        f"⚠️ Forward failed:\n<code>{exc}</code>",
                        parse_mode="HTML",
                    )
                except Exception:
                    pass

            # ── 3. Apply watermark ───────────────────────────────────────────
            await bot.edit_message_text(
                t("processing", lang, pct="0%"), chat_id=chat_id,
                message_id=status_msg.message_id,
            )

            class _S:
                pass

            s = _S()
            for k, v in settings_snapshot.items():
                setattr(s, k, v)

            async def proc_progress(pct: str) -> None:
                try:
                    await bot.edit_message_text(
                        t("processing", lang, pct=pct), chat_id=chat_id,
                        message_id=status_msg.message_id,
                    )
                except Exception:
                    pass

            await apply_watermark(input_path, output_path, s,
                                   progress_callback=proc_progress)

            output_size = os.path.getsize(output_path)

            # ── 4. Upload result to user ─────────────────────────────────────
            await bot.edit_message_text(
                t("uploading", lang, pct="0%"), chat_id=chat_id,
                message_id=status_msg.message_id,
            )
            async with AsyncSessionFactory() as db:
                await update_job_status(db, job_id, "uploading")

            caption = t("done_caption", lang, name=original_filename, size=get_file_size_str(output_size))

            async def up_progress(pct: str) -> None:
                try:
                    await bot.edit_message_text(
                        t("uploading", lang, pct=pct), chat_id=chat_id,
                        message_id=status_msg.message_id,
                    )
                except Exception:
                    pass

            # Thumbnail from watermarked output for correct preview
            out_thumb = await generate_thumbnail(output_path, out_thumb_path)

            await upload_file_telethon(
                chat_id=chat_id, file_path=output_path, caption=caption,
                width=vid_width, height=vid_height, duration=vid_duration,
                thumb_path=out_thumb,
                progress_callback=up_progress,
            )

            async with AsyncSessionFactory() as db:
                await update_job_status(db, job_id, "done")

            # Edit status → show done; send fresh menu below the video
            await bot.edit_message_text(
                t("done_status", lang),
                chat_id=chat_id,
                message_id=status_msg.message_id,
            )
            await bot.send_message(
                chat_id,
                t("what_next", lang),
                reply_markup=main_menu_keyboard(lang),
            )

        except Exception as exc:
            logger.error(f"Job {job_id} failed: {exc}", exc_info=True)
            async with AsyncSessionFactory() as db:
                await update_job_status(db, job_id, "failed", str(exc)[:500])
            try:
                await bot.edit_message_text(
                    t("job_failed", lang, err=str(exc)[:200]),
                    chat_id=chat_id, message_id=status_msg.message_id,
                    parse_mode="HTML", reply_markup=main_menu_keyboard(lang),
                )
            except Exception:
                pass
        finally:
            for p in (input_path, output_path, thumb_path, out_thumb_path):
                await safe_remove(p)

    await task_queue.enqueue(process_task, user.id, job_id)


@router.callback_query(F.data == "cancel_job")
async def cb_cancel_job(call: CallbackQuery, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.message.edit_text(t("cancelled", lang), reply_markup=main_menu_keyboard(lang))
    await call.answer()
