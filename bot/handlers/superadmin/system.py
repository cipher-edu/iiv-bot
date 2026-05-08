import platform
import sys
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.user_repo import UserRepository
from bot.repositories.audit_repo import AuditRepository

router = Router(name="sa_system")


@router.callback_query(F.data == "sa:system")
async def system_status(callback: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    user_stats = await user_repo.count_by_status()
    total_users = sum(user_stats.values())

    import psutil
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        mem_text = f"{memory.used // (1024**2)}MB / {memory.total // (1024**2)}MB ({memory.percent}%)"
        disk_text = f"{disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB ({disk.percent}%)"
        cpu_text = f"{cpu}%"
    except ImportError:
        mem_text = "psutil not installed"
        disk_text = "psutil not installed"
        cpu_text = "psutil not installed"

    text = (
        "📊 <b>Tizim holati</b>\n\n"
        f"{'─' * 30}\n"
        f"🐍 Python: {sys.version.split()[0]}\n"
        f"💻 OS: {platform.system()} {platform.release()}\n"
        f"🕐 Server vaqti: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"{'─' * 30}\n"
        f"🔧 CPU: {cpu_text}\n"
        f"💾 RAM: {mem_text}\n"
        f"💿 Disk: {disk_text}\n"
        f"{'─' * 30}\n"
        f"👥 Foydalanuvchilar: {total_users}\n"
        f"   Faol: {user_stats.get('active', 0)}\n"
        f"   Bloklangan: {user_stats.get('blocked', 0)}\n"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Yangilash", callback_data="sa:system")
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:superadmin"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "sa:maintenance")
async def toggle_maintenance(callback: CallbackQuery):
    await callback.answer(
        "⚠️ Texnik xizmat rejimi — hali implement qilinmagan.\n"
        "Redis flag orqali boshqariladi.",
        show_alert=True,
    )


@router.callback_query(F.data == "sa:logs")
async def system_logs(callback: CallbackQuery, session: AsyncSession):
    audit_repo = AuditRepository(session)
    recent = await audit_repo.get_recent(limit=20)

    text = "📜 <b>Oxirgi amallar (Audit Log)</b>\n\n"
    for log in recent:
        time_str = log.created_at.strftime("%d.%m %H:%M")
        text += f"[{time_str}] {log.action} | user_id={log.user_id}\n"

    if not recent:
        text += "Hali loglar yo'q."

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:superadmin"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
