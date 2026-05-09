from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.certificate import Certificate
from bot.models.user import TelegramUser

router = Router(name="verify")


@router.message(Command("verify"))
async def verify_certificate(
    message: Message, command: CommandObject, session: AsyncSession
):
    if not command.args:
        await message.answer(
            "🔍 <b>Sertifikat tekshirish</b>\n\n"
            "Foydalanish: <code>/verify SERIYA-RAQAM</code>\n"
            "Misol: <code>/verify IIV-2024-A1B2C3D4</code>"
        )
        return

    cert_number = command.args.strip().upper()
    stmt = select(Certificate).where(
        Certificate.certificate_number == cert_number
    )
    cert = (await session.execute(stmt)).scalar_one_or_none()

    if not cert:
        await message.answer(
            f"❌ Sertifikat topilmadi: <code>{cert_number}</code>"
        )
        return

    user_stmt = select(TelegramUser).where(TelegramUser.id == cert.user_id)
    owner = (await session.execute(user_stmt)).scalar_one_or_none()

    is_valid = cert.is_valid and not cert.is_deleted
    status = "✅ <b>HAQIQIY</b>" if is_valid else "❌ <b>BEKOR QILINGAN</b>"

    text = (
        f"🔍 <b>Sertifikat tekshirildi</b>\n\n"
        f"Holati: {status}\n"
        f"Raqami: <code>{cert.certificate_number}</code>\n"
        f"Nomi: {cert.title}\n"
        f"Egasi: {owner.display_name if owner else 'Nomaʼlum'}\n"
        f"Berilgan sana: {cert.issued_date.strftime('%d.%m.%Y')}\n"
    )
    if cert.score_percent is not None:
        text += f"Ball: {cert.score_percent}%\n"

    await message.answer(text)
