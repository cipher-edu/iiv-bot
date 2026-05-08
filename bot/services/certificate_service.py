from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.certificate import Certificate
from bot.repositories.certificate_repo import CertificateRepository
from bot.utils.pdf_generator import generate_certificate_pdf


class CertificateService:
    def __init__(self, session: AsyncSession):
        self.repo = CertificateRepository(session)

    async def issue_certificate(
        self, user_id: int, course_id: int, user_name: str, course_title: str,
    ) -> Certificate:
        existing = await self.repo.has_certificate(user_id, course_id)
        if existing:
            return existing

        cert = await self.repo.issue_certificate(
            user_id=user_id, course_id=course_id, title=course_title,
        )
        pdf_path = generate_certificate_pdf(
            certificate_number=cert.certificate_number,
            user_name=user_name,
            course_title=course_title,
        )
        cert.file_path = str(pdf_path)
        return cert

    async def get_user_certificates(
        self, user_id: int, limit: int = 20
    ) -> Sequence[Certificate]:
        return await self.repo.get_by_filters(user_id=user_id)

    async def verify_certificate(self, cert_number: str) -> Optional[Certificate]:
        from sqlalchemy import select
        from bot.models.certificate import Certificate as CertModel
        stmt = select(CertModel).where(CertModel.certificate_number == cert_number)
        result = await self.repo.session.execute(stmt)
        return result.scalar_one_or_none()
