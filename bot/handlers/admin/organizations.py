from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.user_repo import OrganizationRepository
from bot.core.enums import OrganizationType

router = Router(name="admin_organizations")


class OrgCreateState(StatesGroup):
    waiting_name = State()
    waiting_type = State()


@router.callback_query(F.data == "admin:organizations")
async def admin_organizations(callback: CallbackQuery, session: AsyncSession):
    repo = OrganizationRepository(session)
    orgs = await repo.get_active_all()

    text = "🏢 <b>Tashkilotlar boshqaruvi</b>\n\n"
    type_labels = {"bolim": "Bo'lim", "fakultet": "Fakultet", "kafedra": "Kafedra"}

    for org in orgs:
        text += f"🏢 {org.name} ({type_labels.get(org.org_type, org.org_type)})\n"

    if not orgs:
        text += "Hozircha tashkilotlar yo'q."

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yangi tashkilot", callback_data="admin:org:create")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin:org:create")
async def create_org(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrgCreateState.waiting_name)
    await callback.message.answer("🏢 Tashkilot nomini kiriting:")
    await callback.answer()


@router.message(OrgCreateState.waiting_name, F.text)
async def org_name(message: Message, state: FSMContext):
    await state.update_data(org_name=message.text)
    await state.set_state(OrgCreateState.waiting_type)

    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Bo'lim"), KeyboardButton(text="Fakultet"), KeyboardButton(text="Kafedra")]
        ],
        resize_keyboard=True,
    )
    await message.answer("Tashkilot turini tanlang:", reply_markup=kb)


@router.message(OrgCreateState.waiting_type, F.text)
async def org_type(message: Message, state: FSMContext, session: AsyncSession):
    type_map = {
        "Bo'lim": OrganizationType.DEPARTMENT,
        "Fakultet": OrganizationType.FACULTY,
        "Kafedra": OrganizationType.CHAIR,
    }
    org_type = type_map.get(message.text)
    if not org_type:
        await message.answer("❌ Tugmalardan birini tanlang.")
        return

    data = await state.get_data()
    repo = OrganizationRepository(session)
    await repo.create(name=data["org_name"], org_type=org_type)

    await state.clear()
    await message.answer(f"✅ Tashkilot yaratildi: {data['org_name']} ({message.text})")
