from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models import HairTone


class HairToneRepository:
    model = HairTone

    async def get_all_tones(self, session: AsyncSession) -> list[HairTone]:
        stmt = select(self.model)
        result = await session.execute(stmt)
        return list(result.scalars().all())
