from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Float, Boolean, Text, DateTime, Integer, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WatermarkSettings(Base):
    __tablename__ = "watermark_settings"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    text: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    font: Mapped[str] = mapped_column(String(100), default="Montserrat-Bold")
    size: Mapped[str] = mapped_column(String(10), default="6%")
    color: Mapped[str] = mapped_column(String(50), default="white")
    opacity: Mapped[float] = mapped_column(Float, default=0.8)
    position: Mapped[str] = mapped_column(String(50), default="right_bottom")
    alternation_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    alternation_interval: Mapped[int] = mapped_column(Integer, default=5)
    alternation_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    delay_seconds: Mapped[int] = mapped_column(Integer, default=0)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    file_id: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
