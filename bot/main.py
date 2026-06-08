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
    # Quiet noisy libraries
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


async def on_startup(bot: Bot) -> None:
    logging.getLogger(__name__).info("Starting bot...")
    ensure_dirs()
    await init_db()
    task_queue.start()

    # Verify bot token
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

    # Use MemoryStorage (swap for RedisStorage in production if needed)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register middleware
    dp.update.middleware(DbSessionMiddleware())

    # Register routers
    dp.include_router(setup_routers())

    # Lifecycle hooks
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
