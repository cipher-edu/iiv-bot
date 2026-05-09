"""Generate PDF files for any certificate row whose file_path is empty/missing."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from bot.models.base import async_session_factory, engine
from bot.models.certificate import Certificate
from bot.models.user import TelegramUser
from bot.utils.pdf_generator import generate_certificate_pdf


async def main():
    generated = 0
    skipped = 0
    failed = 0

    async with async_session_factory() as session:
        async with session.begin():
            stmt = select(Certificate).where(Certificate.is_deleted == False)
            certs = (await session.execute(stmt)).scalars().all()

            for cert in certs:
                if cert.file_path and Path(cert.file_path).exists():
                    skipped += 1
                    continue

                user = await session.get(TelegramUser, cert.user_id)
                full_name = (user.display_name if user else f"User #{cert.user_id}")

                try:
                    path = generate_certificate_pdf(
                        full_name=full_name,
                        course_title=cert.title,
                        certificate_number=cert.certificate_number,
                        issued_date=cert.issued_date,
                        score_percent=cert.score_percent,
                    )
                    cert.file_path = path
                    generated += 1
                    print(f"  ✓ {cert.certificate_number} → {path}")
                except Exception as e:
                    failed += 1
                    print(f"  ✗ {cert.certificate_number} ERROR: {e}")

    print(f"\nGenerated: {generated}, Skipped: {skipped}, Failed: {failed}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
