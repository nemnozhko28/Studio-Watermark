import json
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from bot.models import User, WatermarkSettings, Job

logger = logging.getLogger(__name__)


async def upsert_user(
    session: AsyncSession,
    user_id: int,
    username: Optional[str],
    first_name: str,
) -> None:
    """Create or update user record."""
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
        # Fallback to SQLite upsert
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
    """Fetch watermark settings for a user."""
    result = await session.get(WatermarkSettings, user_id)
    return result


async def get_or_create_settings(
    session: AsyncSession, user_id: int
) -> WatermarkSettings:
    """Get existing settings or create defaults."""
    settings = await session.get(WatermarkSettings, user_id)
    if not settings:
        settings = WatermarkSettings(user_id=user_id)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return settings


async def update_watermark_text(
    session: AsyncSession, user_id: int, text: str
) -> None:
    settings = await get_or_create_settings(session, user_id)
    settings.text = text
    await session.commit()


async def update_watermark_font(
    session: AsyncSession, user_id: int, font: str
) -> None:
    settings = await get_or_create_settings(session, user_id)
    settings.font = font
    await session.commit()


async def update_watermark_size(
    session: AsyncSession, user_id: int, size: str
) -> None:
    settings = await get_or_create_settings(session, user_id)
    settings.size = size
    await session.commit()


async def update_watermark_color(
    session: AsyncSession, user_id: int, color: str
) -> None:
    settings = await get_or_create_settings(session, user_id)
    settings.color = color
    await session.commit()


async def update_watermark_opacity(
    session: AsyncSession, user_id: int, opacity: float
) -> None:
    settings = await get_or_create_settings(session, user_id)
    settings.opacity = opacity
    await session.commit()


async def update_watermark_position(
    session: AsyncSession, user_id: int, position: str
) -> None:
    settings = await get_or_create_settings(session, user_id)
    settings.position = position
    await session.commit()


async def update_alternation(
    session: AsyncSession,
    user_id: int,
    enabled: bool,
    interval: int,
    alternation_data: Optional[dict],
) -> None:
    settings = await get_or_create_settings(session, user_id)
    settings.alternation_enabled = enabled
    settings.alternation_interval = interval
    settings.alternation_json = alternation_data
    await session.commit()


async def create_job(
    session: AsyncSession,
    user_id: int,
    file_id: str,
    original_filename: Optional[str] = None,
) -> Job:
    job = Job(user_id=user_id, file_id=file_id, original_filename=original_filename)
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
