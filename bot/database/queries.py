import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.models import User, WatermarkSettings, Job

logger = logging.getLogger(__name__)


async def upsert_user(
    session: AsyncSession,
    user_id: int,
    username: Optional[str],
    first_name: str,
) -> None:
    stmt = (
        pg_insert(User)
        .values(user_id=user_id, username=username, first_name=first_name)
        .on_conflict_do_update(
            index_elements=[User.user_id],
            set_={"username": username, "first_name": first_name},
        )
    )
    try:
        await session.execute(stmt)
        await session.commit()
    except Exception:
        await session.rollback()
        existing = await session.get(User, user_id)
        if existing:
            existing.username = username
            existing.first_name = first_name
        else:
            session.add(User(user_id=user_id, username=username, first_name=first_name))
        await session.commit()


async def get_watermark_settings(
    session: AsyncSession, user_id: int
) -> Optional[WatermarkSettings]:
    return await session.get(WatermarkSettings, user_id)


async def get_or_create_settings(
    session: AsyncSession, user_id: int
) -> WatermarkSettings:
    settings = await session.get(WatermarkSettings, user_id)
    if not settings:
        settings = WatermarkSettings(user_id=user_id)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return settings


def get_lang(settings: WatermarkSettings) -> str:
    """Return language code from settings, defaulting to 'ru'."""
    lang = getattr(settings, "language", None) or "ru"
    return lang if lang in ("ru", "en") else "ru"


async def update_watermark_text(session: AsyncSession, user_id: int, text: str) -> None:
    s = await get_or_create_settings(session, user_id)
    s.text = text
    await session.commit()


async def update_watermark_font(session: AsyncSession, user_id: int, font: str) -> None:
    s = await get_or_create_settings(session, user_id)
    s.font = font
    await session.commit()


async def update_watermark_size(session: AsyncSession, user_id: int, size: str) -> None:
    s = await get_or_create_settings(session, user_id)
    s.size = size
    await session.commit()


async def update_watermark_color(session: AsyncSession, user_id: int, color: str) -> None:
    s = await get_or_create_settings(session, user_id)
    s.color = color
    await session.commit()


async def update_watermark_opacity(session: AsyncSession, user_id: int, opacity: float) -> None:
    s = await get_or_create_settings(session, user_id)
    s.opacity = opacity
    await session.commit()


async def update_watermark_position(session: AsyncSession, user_id: int, position: str) -> None:
    s = await get_or_create_settings(session, user_id)
    s.position = position
    await session.commit()


async def update_watermark_delay(session: AsyncSession, user_id: int, delay_seconds: int) -> None:
    s = await get_or_create_settings(session, user_id)
    s.delay_seconds = delay_seconds
    await session.commit()


async def update_alternation(
    session: AsyncSession,
    user_id: int,
    enabled: bool,
    interval: int,
    alternation_data: Optional[dict],
) -> None:
    s = await get_or_create_settings(session, user_id)
    s.alternation_enabled = enabled
    s.alternation_interval = interval
    s.alternation_json = alternation_data
    await session.commit()


async def update_language(session: AsyncSession, user_id: int, lang: str) -> None:
    s = await get_or_create_settings(session, user_id)
    s.language = lang
    await session.commit()


async def create_job(
    session: AsyncSession,
    user_id: int,
    file_id: str,
    original_filename: Optional[str] = None,
    source_chat_id: Optional[int] = None,
    source_message_id: Optional[int] = None,
) -> Job:
    job = Job(
        user_id=user_id,
        file_id=file_id,
        original_filename=original_filename,
        source_chat_id=source_chat_id,
        source_message_id=source_message_id,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def update_job_status(
    session: AsyncSession,
    job_id: int,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    job = await session.get(Job, job_id)
    if job:
        job.status = status
        if status in ("done", "failed"):
            job.finished_at = datetime.utcnow()
        if error_message:
            job.error_message = error_message
        await session.commit()


async def get_user_jobs(
    session: AsyncSession, user_id: int, limit: int = 10
) -> List[Job]:
    result = await session.execute(
        select(Job)
        .where(Job.user_id == user_id)
        .order_by(Job.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
