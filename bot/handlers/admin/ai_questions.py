from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.repositories.course_repo import CourseRepository

router = Router(name="admin_ai_questions")


class AIGenerateState(StatesGroup):
    waiting_count = State()


@router.callback_query(F.data.startswith("admin:lesson:aigen:"))
async def ai_generate_start(callback: CallbackQuery, state: FSMContext):
    if not (settings.anthropic_api_key or settings.openai_api_key):
        await callback.answer(
            "❌ AI sozlanmagan. Admin .env'da kalit qo'shsin.", show_alert=True
        )
        return

    lesson_id = int(callback.data.split(":")[-1])
    await state.set_state(AIGenerateState.waiting_count)
    await state.update_data(lesson_id=lesson_id)
    await callback.message.answer(
        "🤖 AI nechta savol generatsiya qilsin? (1-10):"
    )
    await callback.answer()


@router.message(AIGenerateState.waiting_count, F.text)
async def ai_generate_run(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    try:
        count = int(message.text.strip())
        if count < 1 or count > 10:
            raise ValueError
    except ValueError:
        await message.answer("❌ 1-10 oralig'ida raqam kiriting.")
        return

    data = await state.get_data()
    lesson_id = data["lesson_id"]
    repo = CourseRepository(session)
    lesson = await repo.get_lesson(lesson_id)
    if not lesson or not lesson.content:
        await message.answer("❌ Dars matni yo'q, AI generatsiya qila olmaydi.")
        await state.clear()
        return

    await message.answer("🤖 AI savol generatsiya qilmoqda...")

    if settings.anthropic_api_key:
        from bot.integrations.ai.claude_client import claude_client
        result = await claude_client.generate_test(
            topic=f"{lesson.title}\n\n{lesson.content[:3000]}", count=count
        )
    else:
        from bot.integrations.ai.openai_client import openai_client
        prompt = (
            f"Quyidagi mavzu bo'yicha {count} ta test savoli yarating "
            f"(har birida 4 javob, to'g'ri javob belgilangan):\n\n"
            f"{lesson.title}\n\n{lesson.content[:3000]}"
        )
        result = await openai_client.send_message(prompt, [])

    await state.clear()
    if not result:
        await message.answer("❌ AI javob bera olmadi.")
        return

    chunks = [result[i : i + 3500] for i in range(0, len(result), 3500)]
    for ch in chunks:
        await message.answer(f"<pre>{ch}</pre>")

    await message.answer(
        "ℹ️ Yuqoridagi savollarni admin panelidan qo'lda kiritib qo'shing."
    )
