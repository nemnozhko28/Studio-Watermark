from aiogram import Router
from .start import router as start_router
from .settings import router as settings_router
from .video import router as video_router


def setup_routers() -> Router:
    main_router = Router()
    main_router.include_router(start_router)
    main_router.include_router(settings_router)
    main_router.include_router(video_router)
    return main_router
