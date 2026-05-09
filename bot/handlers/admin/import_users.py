import io
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser, Organization
from bot.repositories.user_repo import UserRepository, OrganizationRepository
from bot.core.enums import RegistrationStep, UserStatus, Role, UserCategory

router = Router(name="admin_import")


class ImportState(StatesGroup):
    waiting_file = State()


@router.callback_query(F.data == "admin:import")
async def import_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ImportState.waiting_file)
    await callback.message.answer(
        "📥 <b>Excel / CSV import</b>\n\n"
        "Faylni yuboring. Format (sarlavhalar):\n"
        "<code>telegram_id,full_name,phone,category,position,organization</code>\n\n"
        "Qiymatlar:\n"
        "  • <b>category</b>: hodim yoki fuqaro (bo'sh bo'lsa fuqaro)\n"
        "  • <b>organization</b>: tashkilot nomi (avval yaratilgan)\n\n"
        "Telegram ID majburiy. Mavjud foydalanuvchilar yangilanadi."
    )
    await callback.answer()


@router.message(ImportState.waiting_file, F.document)
async def import_run(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
):
    doc = message.document
    if not doc.file_name or not (
        doc.file_name.endswith(".csv") or doc.file_name.endswith(".xlsx")
    ):
        await message.answer("❌ Faqat .csv yoki .xlsx fayl yuboring.")
        return

    file = await bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await bot.download_file(file.file_path, destination=buf)
    buf.seek(0)

    rows = []
    try:
        if doc.file_name.endswith(".csv"):
            import csv
            text = buf.read().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
        else:
            from openpyxl import load_workbook
            wb = load_workbook(buf, read_only=True)
            ws = wb.active
            headers = [c.value for c in next(ws.iter_rows(max_row=1))]
            for row in ws.iter_rows(min_row=2, values_only=True):
                rows.append(dict(zip(headers, row)))
    except Exception as e:
        await message.answer(f"❌ Faylni o'qib bo'lmadi: {e}")
        return

    if not rows:
        await message.answer("❌ Fayl bo'sh.")
        return

    user_repo = UserRepository(session)
    org_repo = OrganizationRepository(session)
    org_cache: dict[str, int] = {}

    created = 0
    updated = 0
    failed = 0

    for row in rows:
        try:
            tg_id = int(row.get("telegram_id") or 0)
            if not tg_id:
                failed += 1
                continue

            full_name = (row.get("full_name") or "").strip() or None
            phone = (row.get("phone") or "").strip() or None
            position = (row.get("position") or "").strip() or None
            cat_raw = (row.get("category") or "").strip().lower()
            category = (
                UserCategory.HODIM
                if cat_raw == "hodim"
                else (UserCategory.FUQARO if cat_raw == "fuqaro" else None)
            )

            org_name = (row.get("organization") or "").strip()
            org_id = None
            if org_name:
                if org_name in org_cache:
                    org_id = org_cache[org_name]
                else:
                    stmt = select(Organization).where(Organization.name == org_name)
                    org = (await session.execute(stmt)).scalar_one_or_none()
                    if org:
                        org_id = org.id
                        org_cache[org_name] = org_id

            existing = await user_repo.get_by_telegram_id(tg_id)
            if existing:
                await user_repo.update_by_id(
                    existing.id,
                    full_name=full_name or existing.full_name,
                    phone=phone or existing.phone,
                    position=position or existing.position,
                    category=category or existing.category,
                    organization_id=org_id or existing.organization_id,
                )
                updated += 1
            else:
                user = TelegramUser(
                    telegram_id=tg_id,
                    full_name=full_name,
                    phone=phone,
                    position=position,
                    category=category,
                    organization_id=org_id,
                    role=Role.USER,
                    status=UserStatus.ACTIVE,
                    registration_step=RegistrationStep.COMPLETED,
                    is_verified=True,
                )
                session.add(user)
                created += 1
        except Exception:
            failed += 1
        await session.flush()

    await state.clear()
    await message.answer(
        f"✅ <b>Import tugadi</b>\n\n"
        f"Yangi: {created}\n"
        f"Yangilangan: {updated}\n"
        f"Xato: {failed}\n"
        f"Jami: {len(rows)}"
    )


@router.message(ImportState.waiting_file)
async def import_wrong_input(message: Message):
    await message.answer("❌ Faqat fayl (.csv yoki .xlsx) yuboring.")
