import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from bot.config import config
from bot.models import User, Job
from bot.services import task_queue

logger = logging.getLogger(__name__)
router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    return user_id == config.admin_id


@router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession) -> None:
    if not is_admin(message.from_user.id):
        return

    total_users = await session.scalar(select(func.count()).select_from(User))
    total_jobs = await session.scalar(select(func.count()).select_from(Job))
    done_jobs = await session.scalar(
        select(func.count()).select_from(Job).where(Job.status == "done")
    )
    failed_jobs = await session.scalar(
        select(func.count()).select_from(Job).where(Job.status == "failed")
    )
    pending_in_queue = task_queue.pending_count

    await message.answer(
        "🛠 <b>Панель администратора</b>\n\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"📋 Всего задач: <b>{total_jobs}</b>\n"
        f"✅ Выполнено: <b>{done_jobs}</b>\n"
        f"❌ Ошибок: <b>{failed_jobs}</b>\n"
        f"⏳ В очереди: <b>{pending_in_queue}</b>",
        parse_mode="HTML",
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession) -> None:
    if not is_admin(message.from_user.id):
        return
    await cmd_admin(message, session)


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, session: AsyncSession) -> None:
    if not is_admin(message.from_user.id):
        return

    text = message.text.removeprefix("/broadcast").strip()
    if not text:
        await message.answer("Использование: /broadcast <текст сообщения>")
        return

    users = await session.execute(select(User.user_id))
    user_ids = [row[0] for row in users.all()]

    sent = 0
    failed = 0
    bot = message.bot
    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception as e:
            logger.warning(f"Broadcast to {uid} failed: {e}")
            failed += 1

    await message.answer(f"📢 Рассылка завершена.\n✅ Отправлено: {sent}\n❌ Ошибок: {failed}")
