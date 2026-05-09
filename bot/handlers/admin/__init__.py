from aiogram import Router

from bot.handlers.admin.menu import router as menu_router
from bot.handlers.admin.dashboard import router as dashboard_router
from bot.handlers.admin.users import router as users_router
from bot.handlers.admin.tests import router as tests_router
from bot.handlers.admin.news import router as news_router
from bot.handlers.admin.broadcast import router as broadcast_router
from bot.handlers.admin.courses import router as courses_router
from bot.handlers.admin.ratings import router as ratings_router
from bot.handlers.admin.certificates import router as certificates_router
from bot.handlers.admin.tasks import router as tasks_router
from bot.handlers.admin.surveys import router as surveys_router
from bot.handlers.admin.library import router as library_router
from bot.handlers.admin.organizations import router as organizations_router
from bot.handlers.admin.export import router as export_router
from bot.handlers.admin.ai_questions import router as ai_questions_router
from bot.handlers.admin.broadcast_segments import router as broadcast_segments_router
from bot.handlers.admin.statistics import router as statistics_router
from bot.handlers.admin.import_users import router as import_users_router
from bot.filters.admin import IsAdminFilter

admin_router = Router(name="admin")
admin_router.message.filter(IsAdminFilter())
admin_router.callback_query.filter(IsAdminFilter())

admin_router.include_routers(
    menu_router,
    dashboard_router,
    users_router,
    tests_router,
    news_router,
    broadcast_router,
    courses_router,
    ratings_router,
    certificates_router,
    tasks_router,
    surveys_router,
    library_router,
    organizations_router,
    export_router,
    ai_questions_router,
    broadcast_segments_router,
    statistics_router,
    import_users_router,
)
