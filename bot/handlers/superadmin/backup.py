import subprocess
from datetime import datetime
from pathlib import Path

from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

from bot.models.user import TelegramUser
from bot.config import settings

router = Router(name="sa_backup")

BACKUP_DIR = Path(__file__).resolve().parent.parent.parent.parent / "backups"
BACKUP_DIR.mkdir(exist_ok=True)


@router.callback_query(F.data == "sa:backup")
async def backup_menu(callback: CallbackQuery):
    backups = sorted(BACKUP_DIR.glob("*.sql*"), reverse=True)[:10]

    text = "💾 <b>Backup boshqaruvi</b>\n\n"
    text += f"📁 Saqlash joyi: {BACKUP_DIR}\n"
    text += f"📦 Mavjud backuplar: {len(list(BACKUP_DIR.glob('*.sql*')))}\n\n"

    if backups:
        text += "<b>Oxirgi 10 ta:</b>\n"
        for b in backups:
            size_mb = b.stat().st_size / (1024 * 1024)
            text += f"  📄 {b.name} ({size_mb:.1f} MB)\n"
    else:
        text += "Hali backup yo'q.\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="💾 Hozir backup qilish", callback_data="sa:backup:now")
    if backups:
        builder.button(text="📥 Oxirgi backupni yuklash", callback_data="sa:backup:download")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:superadmin"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "sa:backup:now")
async def create_backup(callback: CallbackQuery, db_user: TelegramUser):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql"
    filepath = BACKUP_DIR / filename

    try:
        cmd = (
            f"pg_dump -h {settings.db_host} -p {settings.db_port} "
            f"-U {settings.db_user} -d {settings.db_name} "
            f"-f {filepath}"
        )
        env = {"PGPASSWORD": settings.db_password}
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, env=env, timeout=120
        )

        if result.returncode == 0:
            size_mb = filepath.stat().st_size / (1024 * 1024)
            await callback.answer(
                f"✅ Backup yaratildi!\n{filename} ({size_mb:.1f} MB)",
                show_alert=True,
            )
        else:
            await callback.answer(
                f"❌ Backup xatolik: {result.stderr[:100]}",
                show_alert=True,
            )
    except Exception as e:
        await callback.answer(f"❌ Xatolik: {str(e)[:100]}", show_alert=True)


@router.callback_query(F.data == "sa:backup:download")
async def download_backup(callback: CallbackQuery):
    backups = sorted(BACKUP_DIR.glob("*.sql*"), reverse=True)
    if not backups:
        await callback.answer("Backup topilmadi.", show_alert=True)
        return

    latest = backups[0]
    try:
        doc = FSInputFile(str(latest))
        await callback.message.answer_document(doc, caption=f"💾 Backup: {latest.name}")
    except Exception as e:
        await callback.answer(f"❌ Yuklashda xatolik: {str(e)[:100]}", show_alert=True)

    await callback.answer()
