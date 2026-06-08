"""
Entry point for the Telegram Watermark Bot.
"""
import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import config
from bot.database import init_db, close_db
from bot.handlers import setup_routers
from bot.middlewares import DbSessionMiddleware
from bot.services import stop_pyrogram_client, task_queue
from bot.utils import ensure_dirs

# Для теста канала
from pyrogram import enums


def setup_logging() -> None:
    log_dir = Path(config.logs_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "bot.log", encoding="utf-8"),
        ],
    )
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


async def on_startup(bot: Bot) -> None:
    logging.getLogger(__name__).info("Starting bot...")
    ensure_dirs()
    await init_db()
    task_queue.start()

    # === ТЕСТ КАНАЛА ===
    try:
        from bot.services.video_service import get_pyrogram_client
        client = await get_pyrogram_client()
        
        await client.get_chat(config.admin_channel_id)  # Прогрев
        
        await client.send_message(
            config.admin_channel_id,
            "✅ <b>Бот успешно запущен</b>\nТеперь отправляет оригиналы видео в канал.",
            parse_mode=enums.ParseMode.HTML,
        )
        logging.getLogger(__name__).info("✅ Test message to admin channel sent successfully")
    except Exception as e:
        logging.getLogger(__name__).error(f"❌ Cannot send test message to admin channel: {e}")
        try:
            await bot.send_message(
                config.admin_id,
                f"⚠️ <b>Проблема с каналом</b>\n\n<code>{str(e)[:350]}</code>",
                parse_mode=ParseMode.HTML,
            )
        except:
            pass

    me = await bot.get_me()
    logging.getLogger(__name__).info(f"Bot started: @{me.username} (id={me.id})")


async def on_shutdown(bot: Bot) -> None:
    logging.getLogger(__name__).info("Shutting down...")
    await task_queue.stop()
    await stop_pyrogram_client()
    await close_db()
    logging.getLogger(__name__).info("Shutdown complete.")


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DbSessionMiddleware())
    dp.include_router(setup_routers())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Polling stopped.")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
