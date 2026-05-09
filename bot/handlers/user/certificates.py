from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.repositories.certificate_repo import CertificateRepository
from bot.keyboards.user_reply import back_keyboard

router = Router(name="certificates")
router.message.filter(IsRegisteredFilter())


@router.message(F.text == "📜 Sertifikatlar")
async def show_certificates(
    message: Message, session: AsyncSession, db_user: TelegramUser
):
    repo = CertificateRepository(session)
    certificates = await repo.get_user_certificates(db_user.id, limit=20)

    if not certificates:
        await message.answer(
            "📜 Sizda hali sertifikat yo'q.\n\n"
            "Sertifikat olish uchun kurslarni muvaffaqiyatli tugatganingizda "
            "avtomatik beriladi.",
            reply_markup=back_keyboard(),
        )
        return

    text = "📜 <b>Sizning sertifikatlaringiz:</b>\n\n"
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    for cert in certificates:
        text += (
            f"📜 {cert.title}\n"
            f"   📅 {cert.issued_date.strftime('%d.%m.%Y')}\n"
            f"   🔢 {cert.certificate_number}\n\n"
        )
        builder.button(
            text=f"📥 {cert.title[:30]}",
            callback_data=f"cert:download:{cert.id}",
        )

    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("cert:download:"))
async def download_certificate(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    cert_id = int(callback.data.split(":")[-1])
    repo = CertificateRepository(session)
    cert = await repo.get_by_id(cert_id)

    if not cert or cert.user_id != db_user.id:
        await callback.answer("Sertifikat topilmadi.", show_alert=True)
        return

    file_path = cert.file_path
    from pathlib import Path
    if not file_path or not Path(file_path).exists():
        try:
            from bot.utils.pdf_generator import generate_certificate_pdf
            file_path = generate_certificate_pdf(
                full_name=db_user.display_name,
                course_title=cert.title,
                certificate_number=cert.certificate_number,
                issued_date=cert.issued_date,
                score_percent=cert.score_percent,
            )
            cert.file_path = file_path
            await session.flush()
        except Exception as e:
            await callback.answer(
                f"PDF yaratishda xato: {e}", show_alert=True
            )
            return

    try:
        file = FSInputFile(file_path)
        await callback.message.answer_document(
            file,
            caption=(
                f"📜 {cert.title}\n"
                f"🔢 {cert.certificate_number}\n"
                f"🔍 Tekshirish: <code>/verify {cert.certificate_number}</code>"
            ),
        )
    except Exception:
        await callback.answer(
            "Fayl yuborishda xato. Admin bilan bog'laning.", show_alert=True
        )

    await callback.answer()
