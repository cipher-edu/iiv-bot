from aiogram import Router

from bot.handlers.superadmin.system import router as system_router
from bot.handlers.superadmin.security import router as security_router
from bot.handlers.superadmin.backup import router as backup_router
from bot.handlers.superadmin.roles import router as roles_router
from bot.handlers.superadmin.suggestions import router as suggestions_router
from bot.handlers.superadmin.audit_browser import router as audit_browser_router
from bot.filters.admin import IsSuperAdminFilter

superadmin_router = Router(name="superadmin")
superadmin_router.message.filter(IsSuperAdminFilter())
superadmin_router.callback_query.filter(IsSuperAdminFilter())

superadmin_router.include_routers(
    system_router,
    security_router,
    backup_router,
    roles_router,
    suggestions_router,
    audit_browser_router,
)
