from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.registered import IsRegisteredFilter
from bot.models.user import TelegramUser
from bot.repositories.qa_repo import QARepository
from bot.repositories.course_repo import CourseRepository
from bot.repositories.user_repo import UserRepository
from bot.core.enums import Role

router = Router(name="qa")
router.callback_query.filter(IsRegisteredFilter())


class QAState(StatesGroup):
    waiting_question = State()
    waiting_answer = State()


@router.callback_query(F.data.startswith("qa:list:"))
async def qa_list(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    lesson_id = int(callback.data.split(":")[-1])
    repo = QARepository(session)
    questions = await repo.list_for_lesson(lesson_id, limit=20)

    text = "💬 <b>Savol-Javoblar</b>\n\n"
    if not questions:
        text += "Hozircha savollar yo'q. Birinchi bo'lib so'rang!"

    builder = InlineKeyboardBuilder()
    builder.button(text="❓ Savol berish", callback_data=f"qa:ask:{lesson_id}")
    for q in questions:
        icon = "✅" if q.is_resolved else "❓"
        preview = (q.question[:40] + "…") if len(q.question) > 40 else q.question
        builder.button(
            text=f"{icon} {preview} ({q.upvotes}👍 / {len(q.answers)}💬)",
            callback_data=f"qa:view:{q.id}",
        )
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("qa:ask:"))
async def qa_ask_start(
    callback: CallbackQuery, state: FSMContext
):
    lesson_id = int(callback.data.split(":")[-1])
    await state.set_state(QAState.waiting_question)
    await state.update_data(lesson_id=lesson_id)
    await callback.message.answer("❓ Savolingizni yozing:")
    await callback.answer()


@router.message(QAState.waiting_question, F.text)
async def qa_ask_save(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    text = message.text.strip()
    if len(text) < 5:
        await message.answer("❌ Savol juda qisqa.")
        return

    data = await state.get_data()
    repo = QARepository(session)
    await repo.ask_question(data["lesson_id"], db_user.id, text)
    await state.clear()
    await message.answer("✅ Savolingiz qabul qilindi.")


@router.callback_query(F.data.startswith("qa:view:"))
async def qa_view(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: TelegramUser,
):
    qid = int(callback.data.split(":")[-1])
    repo = QARepository(session)
    user_repo = UserRepository(session)
    q = await repo.get_question(qid)
    if not q:
        await callback.answer("Topilmadi.", show_alert=True)
        return

    asker = await user_repo.get_by_id(q.user_id)
    asker_name = asker.display_name if asker else "User"

    text = (
        f"❓ <b>{asker_name}</b> {q.created_at.strftime('%d.%m.%Y')}\n\n"
        f"{q.question}\n\n"
        f"👍 {q.upvotes}\n"
    )

    if q.answers:
        text += "\n<b>Javoblar:</b>\n"
        for a in q.answers:
            answerer = await user_repo.get_by_id(a.user_id)
            mark = " 🎓" if a.is_official else ""
            text += (
                f"\n— {answerer.display_name if answerer else 'User'}{mark}: "
                f"{a.answer} (👍 {a.upvotes})\n"
            )

    builder = InlineKeyboardBuilder()
    builder.button(text="👍 Qo'llab-quvvatlash", callback_data=f"qa:vote:question:{qid}")
    builder.button(text="💬 Javob berish", callback_data=f"qa:answer:{qid}")
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Orqaga", callback_data=f"qa:list:{q.lesson_id}"
        )
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("qa:vote:"))
async def qa_vote(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    parts = callback.data.split(":")
    entity_type = parts[2]
    entity_id = int(parts[3])
    repo = QARepository(session)
    added = await repo.toggle_upvote(db_user.id, entity_type, entity_id)
    await callback.answer("👍 Qo'shildi" if added else "❌ Olib tashlandi")


@router.callback_query(F.data.startswith("qa:answer:"))
async def qa_answer_start(
    callback: CallbackQuery, state: FSMContext
):
    qid = int(callback.data.split(":")[-1])
    await state.set_state(QAState.waiting_answer)
    await state.update_data(question_id=qid)
    await callback.message.answer("💬 Javobingizni kiriting:")
    await callback.answer()


@router.message(QAState.waiting_answer, F.text)
async def qa_answer_save(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    text = message.text.strip()
    if len(text) < 3:
        await message.answer("❌ Javob juda qisqa.")
        return

    data = await state.get_data()
    is_official = Role(db_user.role).has_permission(Role.MODERATOR)
    repo = QARepository(session)
    await repo.add_answer(data["question_id"], db_user.id, text, is_official=is_official)
    await state.clear()
    await message.answer(
        "✅ Javobingiz qabul qilindi."
        + (" (rasmiy belgilandi)" if is_official else "")
    )
