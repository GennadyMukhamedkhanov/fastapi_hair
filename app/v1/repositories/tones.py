from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models import HairTone


class HairToneRepository:
    model = HairTone

    async def get_all_tones(self, session: AsyncSession) -> list[HairTone]:
        stmt = select(self.model)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create_tone(self, session: AsyncSession, tone_name: str) -> HairTone:
        stmt = select(self.model).where(self.model.tone == tone_name)
        result = await session.execute(stmt)
        tone = result.scalar_one_or_none()
        if tone:
            return tone
        new_tone = self.model(tone=tone_name)
        session.add(new_tone)
        await session.commit()
        await session.refresh(new_tone)
        return new_tone
