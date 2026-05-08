from aiogram import Router

from bot.handlers.moderator.review import router as review_router
from bot.handlers.moderator.reports import router as reports_router
from bot.filters.admin import IsModeratorFilter

moderator_router = Router(name="moderator")
moderator_router.message.filter(IsModeratorFilter())
moderator_router.callback_query.filter(IsModeratorFilter())

moderator_router.include_routers(
    review_router,
    reports_router,
)
