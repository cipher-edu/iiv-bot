from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from bot.keyboards.user_reply import back_keyboard

router = Router(name="help")


@router.message(F.text == "❓ Yordam")
@router.message(Command("help"))
async def show_help(message: Message):
    text = (
        "❓ <b>Yordam</b>\n\n"
        "🎓 <b>IIV Ta'lim Platformasi</b> — xodimlarni o'qitish "
        "va malakasini oshirish tizimi.\n\n"
        "📋 <b>Imkoniyatlar:</b>\n"
        "📝 <b>Testlar</b> — bilimingizni sinab ko'ring\n"
        "📚 <b>Kurslar</b> — yangi bilimlar o'rganing\n"
        "📰 <b>Yangiliklar</b> — so'nggi yangiliklar\n"
        "🏆 <b>Reyting</b> — o'z o'rningizni bilib oling\n"
        "📜 <b>Sertifikatlar</b> — yutuqlaringiz tasdigi\n"
        "🎮 <b>Yutuqlar</b> — nishonlar va streaklar\n"
        "📚 <b>Kutubxona</b> — foydali materiallar\n"
        "🤖 <b>AI Yordamchi</b> — sun'iy intellekt bilan suhbat\n"
        "👤 <b>Profil</b> — shaxsiy ma'lumotlar\n\n"
        "🏅 <b>Ball tizimi:</b>\n"
        "• A'lo natija (≥85%): +10 ball\n"
        "• Yaxshi (≥70%): +7 ball\n"
        "• Qoniqarli (≥50%): +4 ball\n"
        "• Ishtirok: +1 ball\n"
        "• Kurs tugatish: +15 ball\n\n"
        "📞 <b>Muammo bo'lsa:</b>\n"
        "Admin bilan bog'laning yoki /start buyrug'ini qayta bosing."
    )
    await message.answer(text, reply_markup=back_keyboard())
