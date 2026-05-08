from aiogram import Router

from bot.handlers.user.start import router as start_router
from bot.handlers.user.registration import router as registration_router
from bot.handlers.user.menu import router as menu_router
from bot.handlers.user.tests import router as tests_router
from bot.handlers.user.courses import router as courses_router
from bot.handlers.user.news import router as news_router
from bot.handlers.user.rating import router as rating_router
from bot.handlers.user.certificates import router as certificates_router
from bot.handlers.user.profile import router as profile_router
from bot.handlers.user.achievements import router as achievements_router
from bot.handlers.user.ai_chat import router as ai_chat_router
from bot.handlers.user.help import router as help_router
from bot.handlers.user.library import router as library_router
from bot.handlers.user.tasks import router as tasks_router
from bot.handlers.user.surveys import router as surveys_router

user_router = Router(name="user")
user_router.include_routers(
    start_router,
    registration_router,
    menu_router,
    tests_router,
    courses_router,
    news_router,
    rating_router,
    certificates_router,
    profile_router,
    achievements_router,
    ai_chat_router,
    help_router,
    library_router,
    tasks_router,
    surveys_router,
)
