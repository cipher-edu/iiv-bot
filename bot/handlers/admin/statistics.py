from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.models.course import Course, Enrollment, Lesson, LessonProgress, LessonRating
from bot.models.test import TestSession
from bot.models.rating import UserRating
from bot.core.enums import UserStatus, CourseStatus

router = Router(name="admin_statistics")


@router.callback_query(F.data == "admin:stats")
async def show_stats(callback: CallbackQuery, session: AsyncSession):
    total_users = (
        await session.execute(
            select(func.count(TelegramUser.id)).where(
                TelegramUser.is_deleted == False
            )
        )
    ).scalar_one()
    active_users = (
        await session.execute(
            select(func.count(TelegramUser.id)).where(
                TelegramUser.status == UserStatus.ACTIVE,
                TelegramUser.is_deleted == False,
            )
        )
    ).scalar_one()
    blocked_users = (
        await session.execute(
            select(func.count(TelegramUser.id)).where(
                TelegramUser.is_blocked == True,
                TelegramUser.is_deleted == False,
            )
        )
    ).scalar_one()

    total_courses = (
        await session.execute(
            select(func.count(Course.id)).where(Course.is_deleted == False)
        )
    ).scalar_one()
    published_courses = (
        await session.execute(
            select(func.count(Course.id)).where(
                Course.status == CourseStatus.PUBLISHED,
                Course.is_deleted == False,
            )
        )
    ).scalar_one()

    total_enrollments = (
        await session.execute(
            select(func.count(Enrollment.id)).where(Enrollment.is_deleted == False)
        )
    ).scalar_one()
    completed_enrollments = (
        await session.execute(
            select(func.count(Enrollment.id)).where(
                Enrollment.is_completed == True,
                Enrollment.is_deleted == False,
            )
        )
    ).scalar_one()

    completion_rate = (
        int(completed_enrollments * 100 / total_enrollments)
        if total_enrollments
        else 0
    )

    total_tests_taken = (
        await session.execute(select(func.count(TestSession.id)))
    ).scalar_one()

    top_users_stmt = (
        select(TelegramUser.full_name, UserRating.total_points)
        .join(UserRating, UserRating.user_id == TelegramUser.id)
        .order_by(UserRating.total_points.desc())
        .limit(5)
    )
    top_users = (await session.execute(top_users_stmt)).all()

    top_courses_stmt = (
        select(Course.title, func.count(Enrollment.id).label("cnt"))
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(Enrollment.is_deleted == False)
        .group_by(Course.id, Course.title)
        .order_by(func.count(Enrollment.id).desc())
        .limit(5)
    )
    top_courses = (await session.execute(top_courses_stmt)).all()

    top_rated_lessons_stmt = (
        select(
            Lesson.title,
            func.avg(LessonRating.stars).label("avg_stars"),
            func.count(LessonRating.id).label("cnt"),
        )
        .join(LessonRating, LessonRating.lesson_id == Lesson.id)
        .group_by(Lesson.id, Lesson.title)
        .having(func.count(LessonRating.id) >= 3)
        .order_by(func.avg(LessonRating.stars).desc())
        .limit(5)
    )
    top_lessons = (await session.execute(top_rated_lessons_stmt)).all()

    text = (
        "📈 <b>Statistika</b>\n\n"
        f"<b>Foydalanuvchilar</b>\n"
        f"  Jami: {total_users}\n"
        f"  Faol: {active_users}\n"
        f"  Bloklangan: {blocked_users}\n\n"
        f"<b>Kurslar</b>\n"
        f"  Jami: {total_courses}\n"
        f"  E'lon qilingan: {published_courses}\n"
        f"  Yozilishlar: {total_enrollments}\n"
        f"  Tugatish foizi: {completion_rate}%\n\n"
        f"<b>Testlar</b>\n"
        f"  Topshirilgan sessiyalar: {total_tests_taken}\n\n"
    )

    if top_users:
        text += "<b>🏆 Top 5 foydalanuvchi:</b>\n"
        for name, pts in top_users:
            text += f"  • {name or '—'} — {pts}\n"
        text += "\n"

    if top_courses:
        text += "<b>📚 Top 5 kurs (yozilish bo'yicha):</b>\n"
        for title, cnt in top_courses:
            text += f"  • {title} — {cnt} ta\n"
        text += "\n"

    if top_lessons:
        text += "<b>⭐ Top baholangan darslar:</b>\n"
        for title, avg, cnt in top_lessons:
            text += f"  • {title} — {float(avg):.1f}⭐ ({cnt})\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Yangilash", callback_data="admin:stats")
    builder.button(text="⬅️ Orqaga", callback_data="admin:menu")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
