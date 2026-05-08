import csv
import io
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.user_repo import UserRepository
from bot.repositories.test_repo import TestResultRepository
from bot.repositories.rating_repo import RatingRepository
from bot.repositories.audit_repo import AuditRepository
from bot.core.enums import AuditAction

router = Router(name="admin_export")


@router.callback_query(F.data == "admin:export")
async def export_menu(callback: CallbackQuery):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Foydalanuvchilar CSV", callback_data="export:users")
    builder.button(text="📝 Test natijalari CSV", callback_data="export:results")
    builder.button(text="🏆 Reyting CSV", callback_data="export:ratings")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))

    await callback.message.edit_text(
        "📤 <b>Ma'lumotlarni export qilish</b>\n\nTurini tanlang:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data == "export:users")
async def export_users(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    repo = UserRepository(session)
    audit_repo = AuditRepository(session)
    users = await repo.get_active_users(limit=10000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Telegram ID", "Ism", "Telefon", "Lavozim", "Tashkilot", "Rol", "Status", "Sana"])

    for u in users:
        writer.writerow([
            u.id, u.telegram_id, u.full_name, u.phone, u.position,
            u.organization.name if u.organization else "",
            u.role, u.status, u.created_at.strftime("%d.%m.%Y"),
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    filename = f"users_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    doc = BufferedInputFile(csv_bytes, filename=filename)

    await audit_repo.log_action(
        action=AuditAction.EXPORT,
        user_id=db_user.id,
        telegram_id=db_user.telegram_id,
        details={"type": "users", "count": len(users)},
    )

    await callback.message.answer_document(doc, caption=f"👥 Foydalanuvchilar: {len(users)} ta")
    await callback.answer()


@router.callback_query(F.data == "export:results")
async def export_results(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    repo = TestResultRepository(session)
    results = await repo.get_all(limit=10000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "User ID", "Test ID", "To'g'ri", "Noto'g'ri", "Ball %", "O'tdimi", "Sana"])

    for r in results:
        writer.writerow([
            r.id, r.user_id, r.test_id, r.correct_count, r.wrong_count,
            r.score_percent, "Ha" if r.is_passed else "Yo'q",
            r.created_at.strftime("%d.%m.%Y %H:%M"),
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    doc = BufferedInputFile(csv_bytes, filename=filename)

    await callback.message.answer_document(doc, caption=f"📝 Test natijalari: {len(results)} ta")
    await callback.answer()


@router.callback_query(F.data == "export:ratings")
async def export_ratings(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    repo = RatingRepository(session)
    user_repo = UserRepository(session)
    ratings = await repo.get_leaderboard(limit=10000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["O'rin", "Ism", "Jami ball", "Haftalik", "Testlar", "Kurslar"])

    for idx, r in enumerate(ratings):
        user = await user_repo.get_by_id(r.user_id)
        name = user.display_name if user else f"#{r.user_id}"
        writer.writerow([
            idx + 1, name, r.total_points, r.weekly_points,
            f"{r.tests_passed}/{r.tests_taken}", r.courses_completed,
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    filename = f"ratings_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    doc = BufferedInputFile(csv_bytes, filename=filename)

    await callback.message.answer_document(doc, caption=f"🏆 Reyting: {len(ratings)} ta")
    await callback.answer()
