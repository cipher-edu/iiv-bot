from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.certificate_repo import CertificateRepository

router = Router(name="admin_certificates")


@router.callback_query(F.data == "admin:certificates")
async def admin_certificates(callback: CallbackQuery, session: AsyncSession):
    repo = CertificateRepository(session)
    total = await repo.count()

    text = (
        "📜 <b>Sertifikatlar boshqaruvi</b>\n\n"
        f"Jami berilgan: {total} ta sertifikat\n\n"
        "Sertifikatlar kurslarni tugatganda avtomatik beriladi.\n"
        "Oylik tekshiruv scheduler orqali amalga oshiriladi."
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Oxirgi sertifikatlar", callback_data="admin:certs:recent")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin:certs:recent")
async def recent_certificates(callback: CallbackQuery, session: AsyncSession):
    repo = CertificateRepository(session)
    certs = await repo.get_all(limit=20)

    text = "📜 <b>Oxirgi sertifikatlar:</b>\n\n"
    for c in certs:
        text += f"🔢 {c.certificate_number} | {c.title} | {c.issued_date}\n"

    if not certs:
        text += "Hali sertifikat berilmagan."

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:certificates"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
