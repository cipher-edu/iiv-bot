from aiogram import Router

from bot.handlers.user import user_router
from bot.handlers.admin import admin_router
from bot.handlers.superadmin import superadmin_router
from bot.handlers.moderator import moderator_router


def setup_routers() -> Router:
    root_router = Router()
    root_router.include_router(superadmin_router)
    root_router.include_router(admin_router)
    root_router.include_router(moderator_router)
    root_router.include_router(user_router)
    return root_router
