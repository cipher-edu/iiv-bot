from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.registered import IsRegisteredFilter
from bot.models.user import TelegramUser
from bot.repositories.notification_repo import NotificationPreferenceRepository

router = Router(name="notification_prefs")
router.message.filter(IsRegisteredFilter())


PREF_LABELS = {
    "news_enabled": "📰 Yangiliklar",
    "test_reminders": "📝 Test eslatmalari",
    "course_reminders": "📚 Kurs eslatmalari",
    "rating_updates": "🏆 Reyting yangilanishlari",
    "achievement_alerts": "🎮 Yutuqlar",
    "quiet_hours_enabled": "🌙 Tinch soatlar (22:00-07:00)",
}


def _build_keyboard(prefs) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for field, label in PREF_LABELS.items():
        value = getattr(prefs, field, True)
        icon = "✅" if value else "❌"
        builder.button(
            text=f"{icon} {label}",
            callback_data=f"notif:toggle:{field}",
        )
    builder.adjust(1)
    return builder


@router.message(F.text == "🔔 Bildirishnomalar")
async def show_notification_prefs(
    message: Message, session: AsyncSession, db_user: TelegramUser
):
    repo = NotificationPreferenceRepository(session)
    prefs = await repo.get_or_create(db_user.id)

    builder = _build_keyboard(prefs)
    await message.answer(
        "🔔 <b>Bildirishnoma sozlamalari</b>\n\n"
        "Har bir tugma orqali yoqish/o'chirish.",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("notif:toggle:"))
async def toggle_pref(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    field = callback.data.split(":")[-1]
    if field not in PREF_LABELS:
        await callback.answer("Noma'lum sozlama.", show_alert=True)
        return

    repo = NotificationPreferenceRepository(session)
    prefs = await repo.get_or_create(db_user.id)
    setattr(prefs, field, not getattr(prefs, field, True))
    await session.flush()

    builder = _build_keyboard(prefs)
    try:
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    except Exception:
        pass
    await callback.answer("✅ Yangilandi.")
