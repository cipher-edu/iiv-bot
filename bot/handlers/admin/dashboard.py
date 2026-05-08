from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.user_repo import UserRepository
from bot.repositories.test_repo import TestRepository, TestResultRepository
from bot.repositories.course_repo import CourseRepository, EnrollmentRepository
from bot.repositories.news_repo import NewsRepository
from bot.keyboards.inline import admin_main_keyboard

router = Router(name="admin_dashboard")


@router.callback_query(F.data == "admin:dashboard")
async def show_dashboard(callback: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    test_repo = TestRepository(session)
    course_repo = CourseRepository(session)
    news_repo = NewsRepository(session)

    user_stats = await user_repo.count_by_status()
    total_users = sum(user_stats.values())
    active_users = user_stats.get("active", 0)
    total_tests = await test_repo.count()
    total_courses = await course_repo.count()
    total_news = await news_repo.count()

    text = (
        "📊 <b>Dashboard — Umumiy statistika</b>\n\n"
        f"{'─' * 30}\n"
        f"👥 <b>Foydalanuvchilar:</b>\n"
        f"   Jami: {total_users}\n"
        f"   Faol: {active_users}\n"
        f"   Kutilmoqda: {user_stats.get('pending', 0)}\n"
        f"   Bloklangan: {user_stats.get('blocked', 0)}\n\n"
        f"📝 <b>Kontent:</b>\n"
        f"   Testlar: {total_tests}\n"
        f"   Kurslar: {total_courses}\n"
        f"   Yangiliklar: {total_news}\n"
        f"{'─' * 30}\n"
    )

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin:dashboard"))
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
