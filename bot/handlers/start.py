import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import upsert_user, get_user_jobs
from bot.keyboards import main_menu_keyboard
from bot.config import POSITIONS

logger = logging.getLogger(__name__)
router = Router(name="start")


async def _register_user(message: Message, session: AsyncSession) -> None:
    user = message.from_user
    await upsert_user(
        session=session,
        user_id=user.id,
        username=user.username,
        first_name=user.first_name or "Без имени",
    )


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    await _register_user(message, session)
    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "Я помогу добавить текстовый водяной знак на ваше видео.\n"
        "Выберите действие:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery) -> None:
    await call.message.edit_text(
        "ℹ️ <b>Как пользоваться ботом:</b>\n\n"
        "1️⃣ Откройте <b>⚙️ Настройки водяного знака</b> и задайте текст, шрифт, цвет, позицию.\n"
        "2️⃣ Нажмите <b>🎥 Добавить видео</b> и отправьте файл.\n"
        "3️⃣ Бот обработает видео и вернёт вам результат.\n\n"
        "<b>Поддерживаемые форматы:</b> mp4, mov, mkv, avi, webm\n"
        "<b>Максимальный размер:</b> до 2 ГБ\n\n"
        "📂 В разделе <b>Мои задачи</b> можно посмотреть историю обработок.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "my_jobs")
async def cb_my_jobs(call: CallbackQuery, session: AsyncSession) -> None:
    jobs = await get_user_jobs(session, call.from_user.id)

    if not jobs:
        await call.message.edit_text(
            "📂 <b>Мои задачи</b>\n\nУ вас пока нет обработанных видео.",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML",
        )
        await call.answer()
        return

    STATUS_EMOJI = {
        "pending": "⏳",
        "downloading": "📥",
        "processing": "⚙️",
        "uploading": "📤",
        "done": "✅",
        "failed": "❌",
    }

    lines = ["📂 <b>Мои задачи (последние 10):</b>\n"]
    for job in jobs:
        emoji = STATUS_EMOJI.get(job.status, "❓")
        date_str = job.created_at.strftime("%d.%m.%Y %H:%M")
        name = job.original_filename or f"Задача #{job.id}"
        lines.append(f"{emoji} <b>#{job.id}</b> — {name}\n   📅 {date_str} | Статус: {job.status}")

    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "settings_done")
async def cb_settings_done(call: CallbackQuery) -> None:
    await call.message.edit_text(
        "✅ Настройки сохранены!\n\nТеперь отправьте видео для обработки.",
        reply_markup=main_menu_keyboard(),
    )
    await call.answer("Настройки сохранены!")
