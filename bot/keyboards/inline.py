from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def paginated_keyboard(
    items: list[tuple[str, str]],
    page: int,
    total_pages: int,
    prefix: str,
    row_width: int = 1,
    back_button: Optional[str] = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for text, callback_data in items:
        builder.button(text=text, callback_data=callback_data)
    builder.adjust(row_width)

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:page:{page - 1}")
        )
    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop")
    )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:page:{page + 1}")
        )

    if nav_buttons and total_pages > 1:
        builder.row(*nav_buttons)

    if back_button:
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_button)
        )

    return builder.as_markup()


def confirmation_keyboard(
    confirm_data: str, cancel_data: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha", callback_data=confirm_data)
    builder.button(text="❌ Yo'q", callback_data=cancel_data)
    builder.adjust(2)
    return builder.as_markup()


def test_options_keyboard(
    options: list[tuple[int, str]], session_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    labels = ["A", "B", "C", "D", "E", "F"]
    for idx, (option_id, text) in enumerate(options):
        label = labels[idx] if idx < len(labels) else str(idx + 1)
        builder.button(
            text=f"{label}) {text[:50]}",
            callback_data=f"test:answer:{session_id}:{option_id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def course_modules_keyboard(
    modules: list[tuple[int, str, bool]], course_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for module_id, title, is_completed in modules:
        icon = "✅" if is_completed else "📖"
        builder.button(
            text=f"{icon} {title}",
            callback_data=f"course:module:{course_id}:{module_id}",
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="courses:list")
    )
    return builder.as_markup()


def admin_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = [
        ("📊 Dashboard", "admin:dashboard"),
        ("👥 Foydalanuvchilar", "admin:users"),
        ("📝 Testlar", "admin:tests"),
        ("📚 Kurslar", "admin:courses"),
        ("📰 Yangiliklar", "admin:news"),
        ("🏆 Reyting", "admin:ratings"),
        ("📜 Sertifikatlar", "admin:certificates"),
        ("📋 Vazifalar", "admin:tasks"),
        ("📊 So'rovnomalar", "admin:surveys"),
        ("📚 Kutubxona", "admin:library"),
        ("🏢 Tashkilotlar", "admin:organizations"),
        ("📢 Broadcast", "admin:broadcast"),
        ("📤 Export", "admin:export"),
    ]
    for text, data in buttons:
        builder.button(text=text, callback_data=data)
    builder.adjust(2)
    return builder.as_markup()


def superadmin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = [
        ("🔐 Xavfsizlik", "sa:security"),
        ("👥 Rollar", "sa:roles"),
        ("⚙️ Sozlamalar", "sa:settings"),
        ("💾 Backup", "sa:backup"),
        ("📋 Audit Log", "sa:audit"),
        ("🔧 Texnik xizmat", "sa:maintenance"),
        ("📊 Tizim holati", "sa:system"),
        ("📜 Loglar", "sa:logs"),
    ]
    for text, data in buttons:
        builder.button(text=text, callback_data=data)
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu")
    )
    return builder.as_markup()
