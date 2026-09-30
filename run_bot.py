import asyncio
import logging
import os
import socket
import sys
from pathlib import Path


def _prefer_reachable_hosts() -> None:
    """Compose hostnames do not resolve when the bot runs on the developer machine."""
    if os.environ.get("DB_HOST") not in (None, "", "postgres"):
        return
    try:
        socket.getaddrinfo("postgres", 5432)
    except OSError:
        os.environ["DB_HOST"] = "127.0.0.1"
        os.environ.setdefault("REDIS_HOST", "127.0.0.1")
        os.environ.setdefault("MINIO_HOST", "127.0.0.1")


_prefer_reachable_hosts()

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    MenuButtonWebApp,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("iiv_edubot")

def load_env_variables() -> dict[str, str]:
    """Parse .env file directly without external dependencies."""
    env_vars: dict[str, str] = {}
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        env_vars[k] = v
        except Exception as e:
            logger.warning(f".env o'qishda xatolik: {e}")
    return env_vars

ENV = load_env_variables()

BOT_TOKEN = os.environ.get("BOT_TOKEN") or ENV.get("BOT_TOKEN", "")
WEB_APP_URL = os.environ.get("WEB_APP_URL") or ENV.get(
    "WEB_APP_URL", "https://frozen-underlying-hollow-jumping.trycloudflare.com"
).rstrip("/")

class IPv4Session(AiohttpSession):
    """Force IPv4 TCPConnector for reliable connectivity in local environments."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._connector_init["family"] = socket.AF_INET

dp = Dispatcher(storage=MemoryStorage())


class GateState(StatesGroup):
    login_id = State()
    login_password = State()
    reg_name = State()
    reg_phone = State()
    reg_position = State()
    reg_login = State()
    reg_password = State()

def get_webapp_url() -> str:
    return WEB_APP_URL.rstrip("/")

def build_inline_menu(url: str, is_staff: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="🚀 Platformani ochish (Web App)",
                web_app=WebAppInfo(url=url),
            )
        ],
        [
            InlineKeyboardButton(
                text="📚 Kurslar katalogi",
                web_app=WebAppInfo(url=f"{url}/courses"),
            ),
            InlineKeyboardButton(
                text="📝 Sinov testlari",
                web_app=WebAppInfo(url=f"{url}/tests"),
            ),
        ],
        [
            InlineKeyboardButton(
                text="🏆 Reyting & Ballar",
                web_app=WebAppInfo(url=f"{url}/rating"),
            ),
            InlineKeyboardButton(
                text="🤖 AI Tyutor",
                web_app=WebAppInfo(url=f"{url}/ai-tutor"),
            ),
        ],
        [
            InlineKeyboardButton(
                text="👤 Profil & Sertifikatlar",
                web_app=WebAppInfo(url=f"{url}/profile"),
            ),
        ],
    ]
    if is_staff:
        rows.append(
            [
                InlineKeyboardButton(
                    text="⚙️ Admin Dashboard",
                    web_app=WebAppInfo(url=f"{url}/admin"),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def gate_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="🔐 Kirish", callback_data="gate:login"),
            InlineKeyboardButton(text="📝 Ro'yxatdan o'tish", callback_data="gate:register"),
        ]]
    )


def category_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="🧑‍💼 Hodim", callback_data="cat:hodim"),
            InlineKeyboardButton(text="🧍 Fuqaro", callback_data="cat:fuqaro"),
        ]]
    )


def account_title(is_staff: bool, category: str) -> str:
    if is_staff:
        return "To'liq administrator"
    if category == "hodim":
        return "Hodim"
    if category == "fuqaro":
        return "Fuqaro"
    return "Ro'yxatdan o'tgan foydalanuvchi"


def _tg_payload(tg) -> dict:
    return {
        "id": tg.id,
        "first_name": tg.first_name or "",
        "last_name": tg.last_name or "",
        "username": tg.username,
    }


async def open_account(tg) -> tuple[str, bool, str]:
    """Return mode (ready|choose), staff access, and display name."""
    from bot.api.service import account_on_start, is_superadmin_user
    from bot.models.base import async_session_factory

    async with async_session_factory() as session:
        db_user, mode = await account_on_start(session, _tg_payload(tg))
        staff = is_superadmin_user(db_user)
        category = str(db_user.category) if db_user.category else ""
        await session.commit()
        logger.info("Start: tg=%s mode=%s role=%s category=%s", tg.id, mode, db_user.role, category)
        return mode, staff, category

def build_reply_keyboard(url: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 O'quv Platformasi (Web App)",
                    web_app=WebAppInfo(url=url),
                )
            ],
            [
                KeyboardButton(text="📚 Kurslar"),
                KeyboardButton(text="📝 Testlar"),
            ],
            [
                KeyboardButton(text="🏆 Reyting"),
                KeyboardButton(text="🤖 AI Tyutor"),
            ],
            [
                KeyboardButton(text="👤 Profil"),
                KeyboardButton(text="ℹ️ Ma'lumot"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

async def send_platform_menu(
    message: Message, bot: Bot, *, is_staff: bool, title: str, first_name: str | None = None
) -> None:
    url = get_webapp_url()
    if not first_name:
        first_name = message.from_user.first_name if message.from_user else "Xodim"
    try:
        await bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="📱 O'quv platformasi",
                web_app=WebAppInfo(url=url),
            ),
        )
    except Exception as e:
        logger.warning(f"Could not set menu button for user: {e}")

    welcome_text = (
        f"Assalomu alaykum, hurmatli <b>{first_name}</b>! 👋\n\n"
        f"Hisobingiz: <b>{title}</b>.\n\n"
        f"🎓 <b>IIV EduBot Ta'lim Platformasiga xush kelibsiz!</b>\n\n"
        f"👇 <b>Quyidagi tugmani bosing va ilovani ishga tushiring:</b>"
    )
    await message.answer(
        welcome_text,
        reply_markup=build_inline_menu(url, is_staff=is_staff),
        parse_mode=ParseMode.HTML,
    )
    await message.answer(
        "⚡️ Doimiy boshqaruv menyusi faollashtirildi:",
        reply_markup=build_reply_keyboard(url),
    )


@dp.message(CommandStart())
async def handle_start(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    tg = message.from_user
    if tg is None:
        return
    try:
        mode, is_staff, category = await open_account(tg)
    except Exception:
        logger.exception("Start hisobini ochishda xato")
        mode, is_staff, category = "choose", False, ""
    if mode == "choose":
        await message.answer(
            f"Assalomu alaykum, <b>{tg.first_name}</b>! 👋\n\n"
            "Davom etish uchun tanlang:\n"
            "🔐 <b>Kirish</b> — login va parol\n"
            "📝 <b>Ro'yxatdan o'tish</b> — hodim yoki fuqaro sifatida",
            reply_markup=gate_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return
    await send_platform_menu(
        message,
        bot,
        is_staff=is_staff,
        title=account_title(is_staff, category),
        first_name=tg.first_name,
    )


@dp.callback_query(F.data == "gate:login")
async def begin_login(query: CallbackQuery, state: FSMContext):
    await state.set_state(GateState.login_id)
    await query.answer()
    if query.message:
        await query.message.answer("Loginni yuboring:")


@dp.callback_query(F.data == "gate:register")
async def begin_register(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.answer()
    if query.message:
        await query.message.answer(
            "Qanday ro'yxatdan o'tasiz?\n"
            "🧑‍💼 <b>Hodim</b> — F.I.O, telefon va lavozim\n"
            "🧍 <b>Fuqaro</b> — F.I.O va telefon",
            reply_markup=category_keyboard(),
            parse_mode=ParseMode.HTML,
        )


@dp.callback_query(F.data.in_({"cat:hodim", "cat:fuqaro"}))
async def choose_category(query: CallbackQuery, state: FSMContext):
    category = (query.data or "cat:fuqaro").split(":", 1)[1]
    await state.set_state(GateState.reg_name)
    await state.update_data(category=category)
    await query.answer()
    if query.message:
        label = "Hodim" if category == "hodim" else "Fuqaro"
        await query.message.answer(
            f"Toifa: <b>{label}</b>\n\nTo'liq ismingizni yozing (F.I.O):",
            parse_mode=ParseMode.HTML,
        )


@dp.message(GateState.login_id, F.text)
async def login_id(message: Message, state: FSMContext):
    login = (message.text or "").strip()
    if len(login) < 3:
        await message.answer("Login kamida 3 ta belgi bo'lsin.")
        return
    await state.update_data(login=login)
    await state.set_state(GateState.login_password)
    await message.answer("Parolni yuboring:")


@dp.message(GateState.login_password, F.text)
async def login_password(message: Message, state: FSMContext, bot: Bot):
    password = message.text or ""
    data = await state.get_data()
    tg = message.from_user
    try:
        from bot.api.service import is_superadmin_user, login_with_password
        from bot.models.base import async_session_factory

        async with async_session_factory() as session:
            user = await login_with_password(
                session, data.get("login") or "", password, _tg_payload(tg) if tg else None
            )
            staff = is_superadmin_user(user)
            category = str(user.category) if user.category else ""
            name = user.display_name
            await session.commit()
    except ValueError as exc:
        await message.answer(f"{exc}\n\nParolni qayta yuboring yoki /start bosing.")
        return
    except Exception:
        logger.exception("Kirishda xato")
        await message.answer("Kirishda xato. /start ni qayta bosing.")
        await state.clear()
        return
    await state.clear()
    await send_platform_menu(
        message,
        bot,
        is_staff=staff,
        title=account_title(staff, category),
        first_name=name,
    )


@dp.message(GateState.reg_name, F.text)
async def reg_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if len(name) < 3:
        await message.answer("Ism juda qisqa. To'liq F.I.O yozing.")
        return
    await state.update_data(full_name=name)
    await state.set_state(GateState.reg_phone)
    await message.answer("Telefon raqamingizni yuboring:")


@dp.message(GateState.reg_phone, F.text)
async def reg_phone(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    digits = phone.replace("+", "").replace(" ", "").replace("-", "")
    if not digits.isdigit() or len(digits) < 9:
        await message.answer("Telefon raqamni to'g'ri kiriting.")
        return
    data = await state.get_data()
    await state.update_data(phone=phone)
    if data.get("category") == "hodim":
        await state.set_state(GateState.reg_position)
        await message.answer("Lavozimingizni yozing. Bo'sh qoldirish uchun - yuboring.")
        return
    await state.set_state(GateState.reg_login)
    await message.answer("Login tanlang (lotin harfi va raqam):")


@dp.message(GateState.reg_position, F.text)
async def reg_position(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    await state.update_data(position="" if text == "-" else text)
    await state.set_state(GateState.reg_login)
    await message.answer("Login tanlang (lotin harfi va raqam):")


@dp.message(GateState.reg_login, F.text)
async def reg_login(message: Message, state: FSMContext):
    login = (message.text or "").strip()
    await state.update_data(login=login)
    await state.set_state(GateState.reg_password)
    await message.answer("Parol o'ylab toping (kamida 6 ta belgi):")


@dp.message(GateState.reg_password, F.text)
async def reg_password(message: Message, state: FSMContext, bot: Bot):
    password = message.text or ""
    data = await state.get_data()
    tg = message.from_user
    try:
        from bot.api.service import is_superadmin_user, register_account
        from bot.models.base import async_session_factory

        async with async_session_factory() as session:
            user = await register_account(
                session,
                full_name=data.get("full_name") or "",
                phone=data.get("phone") or "",
                category=data.get("category") or "fuqaro",
                login=data.get("login") or "",
                password=password,
                position=data.get("position") or "",
                telegram_user=_tg_payload(tg) if tg else None,
            )
            staff = is_superadmin_user(user)
            category = str(user.category) if user.category else ""
            await session.commit()
    except ValueError as exc:
        await state.set_state(GateState.reg_login)
        await message.answer(f"{exc}\n\nBoshqa login yuboring:")
        return
    except Exception:
        logger.exception("Ro'yxatdan o'tishda xato")
        await state.clear()
        await message.answer("Ro'yxatdan o'tishda xato. /start ni qayta bosing.")
        return
    await state.clear()
    await send_platform_menu(
        message,
        bot,
        is_staff=staff,
        title=account_title(staff, category),
        first_name=tg.first_name if tg else None,
    )

@dp.message(F.text == "📚 Kurslar")
@dp.message(Command("courses"))
async def handle_courses(message: Message):
    url = f"{get_webapp_url()}/courses"
    await message.answer(
        "📚 <b>Sohaviy kurslar katalogi</b>\n\n"
        "O'zingizga qiziq bo'lgan yo'nalishni tanlang va video-darslarni tomosha qiling:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📚 Kurslar katalogini ochish", web_app=WebAppInfo(url=url))]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )

@dp.message(F.text == "📝 Testlar")
@dp.message(Command("tests"))
async def handle_tests(message: Message):
    url = f"{get_webapp_url()}/tests"
    await message.answer(
        "📝 <b>Attestatsiya va sinov testlari</b>\n\n"
        "Bilimingizni sinab ko'ring, vaqt bilan bellashing va reyting ballaringizni oshiring:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📝 Testlarni boshlash", web_app=WebAppInfo(url=url))]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )

@dp.message(F.text == "🏆 Reyting")
@dp.message(Command("rating"))
async def handle_rating(message: Message):
    url = f"{get_webapp_url()}/rating"
    await message.answer(
        "🏆 <b>Peshqadamlar shohsupasi</b>\n\n"
        "Barcha xodimlar va tinglovchilar orasida o'z o'rningizni ko'ring:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏆 Reytingni ko'rish", web_app=WebAppInfo(url=url))]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )

@dp.message(F.text == "🤖 AI Tyutor")
@dp.message(Command("ai"))
async def handle_ai_tutor(message: Message):
    url = f"{get_webapp_url()}/ai-tutor"
    await message.answer(
        "🤖 <b>AI Tyutor — Intellektual o'quv maslahatchisi</b>\n\n"
        "Istalgan qonunchilik, ichki ishlar sohaviy qoidalari yoki o'quv mavzulari bo'yicha savol bering:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🤖 AI Tyutor bilan muloqot", web_app=WebAppInfo(url=url))]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )

@dp.message(F.text == "👤 Profil")
@dp.message(Command("profile"))
async def handle_profile(message: Message):
    url = f"{get_webapp_url()}/profile"
    await message.answer(
        "👤 <b>Shaxsiy kabinet & Sertifikatlar</b>\n\n"
        "O'zlashtirish darajangiz, to'plagan nishonlaringiz va QR-kodli sertifikatlaringiz:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👤 Profilni ochish", web_app=WebAppInfo(url=url))]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )

@dp.message(Command("admin"))
async def handle_admin(message: Message):
    tg = message.from_user
    staff = False
    if tg is not None:
        try:
            _mode, staff, _name = await open_account(tg)
        except Exception:
            logger.exception("Admin tekshiruvida xato")
    if not staff:
        await message.answer("Bu bo'lim siz uchun yopiq.")
        return
    url = f"{get_webapp_url()}/admin"
    await message.answer(
        "⚙️ <b>Admin Boshqaruv Paneli</b>\n\n"
        "Kurslar, testlar, foydalanuvchilar va tizim auditini boshqarish:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚙️ Admin panelga o'tish", web_app=WebAppInfo(url=url))]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )

@dp.message(F.text == "ℹ️ Ma'lumot")
@dp.message(Command("help"))
async def handle_help(message: Message):
    url = get_webapp_url()
    await message.answer(
        "ℹ️ <b>IIV EduBot Platformasi qo'llanmasi</b>\n\n"
        "• Har doim pastdagi <b>📱 O'quv Platformasi</b> tugmasi orqali to'liq interaktiv Web App'ga kirishingiz mumkin.\n"
        "• Telegram menyusi chap pastki qismida ham doimiy <b>📱 O'quv platformasi</b> tugmasi mavjud.\n"
        "• Barcha savollar bo'yicha <b>🤖 AI Tyutor</b> xizmatingizda!\n\n"
        "Ilovani ochish uchun quyidagi tugmani bosing:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Web App'ni ochish", web_app=WebAppInfo(url=url))]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )

@dp.message()
async def fallback_handler(message: Message):
    url = get_webapp_url()
    await message.answer(
        "📱 <b>IIV EduBot O'quv Platformasini ochish:</b>\n\n"
        "Platformaning barcha imkoniyatlaridan to'liq foydalanish uchun quyidagi tugmani bosing:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Platformani ochish (Web App)", web_app=WebAppInfo(url=url))]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )

async def main():
    logger.info("Bot tayyorlanmoqda...")
    logger.info("Bot Token: %s...%s", BOT_TOKEN[:10], BOT_TOKEN[-5:])
    logger.info("Web App URL: %s", WEB_APP_URL)

    session = IPv4Session()
    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    try:
        me = await bot.get_me()
        logger.info("Bot muvaffaqiyatli ulandi: @%s (ID: %d, Ism: %s)", me.username, me.id, me.first_name)

        # Set global Menu Button for all users
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="📱 O'quv platformasi",
                    web_app=WebAppInfo(url=WEB_APP_URL),
                )
            )
            logger.info("Global Chat Menu Button o'rnatildi: %s", WEB_APP_URL)
        except Exception as e:
            logger.warning(f"Global menu button xatosi: {e}")

        # Drop pending webhook and old updates so bot responds instantly
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Eski bildirishnomalar tozalandi. Polling boshlanmoqda...")

        await dp.start_polling(bot)
    except Exception as e:
        logger.critical("Bot ishlashida xatolik: %s", e, exc_info=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
