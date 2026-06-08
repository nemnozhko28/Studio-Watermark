import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import upsert_user, get_user_jobs, get_or_create_settings
from bot.database.queries import get_lang
from bot.keyboards import main_menu_keyboard
from bot.i18n import t

logger = logging.getLogger(__name__)
router = Router(name="start")


async def _register_user(message: Message, session: AsyncSession) -> None:
    user = message.from_user
    await upsert_user(
        session=session,
        user_id=user.id,
        username=user.username,
        first_name=user.first_name or "—",
    )


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    await _register_user(message, session)
    settings = await get_or_create_settings(session, message.from_user.id)
    lang = get_lang(settings)
    await message.answer(
        t("welcome", lang, name=message.from_user.first_name),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.message.edit_text(
        t("help_text", lang),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "my_jobs")
async def cb_my_jobs(call: CallbackQuery, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    jobs = await get_user_jobs(session, call.from_user.id)

    if not jobs:
        await call.message.edit_text(
            t("no_jobs", lang),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="HTML",
        )
        await call.answer()
        return

    STATUS_KEY = {
        "pending":     "job_status_pending",
        "downloading": "job_status_downloading",
        "processing":  "job_status_processing",
        "uploading":   "job_status_uploading",
        "done":        "job_status_done",
        "failed":      "job_status_failed",
    }

    lines = [t("jobs_header", lang)]
    for job in jobs:
        emoji = t(STATUS_KEY.get(job.status, "job_status_failed"), lang)
        date_str = job.created_at.strftime("%d.%m.%Y %H:%M")
        name = job.original_filename or f"#{job.id}"
        lines.append(f"{emoji} <b>#{job.id}</b> — {name}\n   📅 {date_str} | {job.status}")

    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "settings_done")
async def cb_settings_done(call: CallbackQuery, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.message.edit_text(
        t("settings_done_msg", lang),
        reply_markup=main_menu_keyboard(lang),
    )
    await call.answer(t("settings_done_toast", lang))
