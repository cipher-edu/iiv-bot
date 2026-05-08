from typing import Optional, Sequence
from datetime import date
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.certificate import Certificate, CertificateTemplate
from bot.repositories.base import BaseRepository


class CertificateRepository(BaseRepository[Certificate]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Certificate)

    async def get_user_certificates(
        self, user_id: int, offset: int = 0, limit: int = 10
    ) -> Sequence[Certificate]:
        stmt = (
            select(Certificate)
            .where(
                Certificate.user_id == user_id,
                Certificate.is_valid == True,
                Certificate.is_deleted == False,
            )
            .order_by(Certificate.issued_date.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_number(self, cert_number: str) -> Optional[Certificate]:
        stmt = select(Certificate).where(
            Certificate.certificate_number == cert_number
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_certificate(self, user_id: int, course_id: int) -> bool:
        stmt = select(Certificate).where(
            Certificate.user_id == user_id,
            Certificate.course_id == course_id,
            Certificate.is_valid == True,
            Certificate.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def issue_certificate(
        self,
        user_id: int,
        course_id: int,
        title: str,
        score_percent: Optional[int] = None,
        template_id: Optional[int] = None,
    ) -> Certificate:
        cert_number = f"IIV-{date.today().year}-{uuid.uuid4().hex[:8].upper()}"
        return await self.create(
            user_id=user_id,
            course_id=course_id,
            title=title,
            certificate_number=cert_number,
            issued_date=date.today(),
            score_percent=score_percent,
            template_id=template_id,
        )

    async def get_default_template(self) -> Optional[CertificateTemplate]:
        stmt = select(CertificateTemplate).where(
            CertificateTemplate.is_default == True,
            CertificateTemplate.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
