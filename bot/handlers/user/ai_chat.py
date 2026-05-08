from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.keyboards.user_reply import back_keyboard
from bot.config import settings

router = Router(name="ai_chat")
router.message.filter(IsRegisteredFilter())


class AIChatState(StatesGroup):
    chatting = State()


@router.message(F.text == "🤖 AI Yordamchi")
async def start_ai_chat(message: Message, state: FSMContext):
    if not settings.ai_enabled:
        await message.answer(
            "🤖 AI yordamchi hozircha o'chirilgan.",
            reply_markup=back_keyboard(),
        )
        return

    await state.set_state(AIChatState.chatting)
    await message.answer(
        "🤖 <b>AI Yordamchi</b>\n\n"
        "Menga savolingizni yozing. Men sizga ta'lim va kasbiy "
        "rivojlanish bo'yicha yordam beraman.\n\n"
        "Chiqish uchun ⬅️ Orqaga tugmasini bosing.",
        reply_markup=back_keyboard(),
    )


@router.message(AIChatState.chatting, F.text)
async def process_ai_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    if message.text == "⬅️ Orqaga":
        await state.clear()
        from bot.keyboards.user_reply import main_menu_keyboard
        await message.answer("Asosiy menyu:", reply_markup=main_menu_keyboard())
        return

    user_message = message.text
    waiting_msg = await message.answer("🤔 O'ylayapman...")

    try:
        if settings.anthropic_api_key:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            response = await client.messages.create(
                model=settings.ai_model,
                max_tokens=settings.ai_max_tokens,
                system=(
                    "Siz IIV ta'lim platformasining AI yordamchisisiz. "
                    "Foydalanuvchilarga o'zbek tilida ta'lim, kasbiy rivojlanish, "
                    "axborot texnologiyalari va kiberxavfsizlik bo'yicha yordam berasiz. "
                    "Javoblar qisqa, aniq va foydali bo'lsin."
                ),
                messages=[{"role": "user", "content": user_message}],
            )
            ai_response = response.content[0].text
        elif settings.openai_api_key:
            import openai
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=settings.ai_max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Siz IIV ta'lim platformasining AI yordamchisisiz. "
                            "O'zbek tilida javob bering."
                        ),
                    },
                    {"role": "user", "content": user_message},
                ],
            )
            ai_response = response.choices[0].message.content
        else:
            ai_response = "AI xizmati sozlanmagan. Admin bilan bog'laning."

        await waiting_msg.delete()
        await message.answer(f"🤖 {ai_response}", reply_markup=back_keyboard())

    except Exception as e:
        await waiting_msg.delete()
        await message.answer(
            "❌ AI xizmatida xatolik yuz berdi. Keyinroq urinib ko'ring.",
            reply_markup=back_keyboard(),
        )
