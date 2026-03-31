from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.common.models.hairs import HairTone
from app.v1.repositories.common import CommonRepository


class HairTonesRepository(CommonRepository):
    model = HairTone

    async def get_all_hair_tones(self, db: AsyncSession):
        stmt = select(self.model).order_by(self.model.tone)
        result = await db.execute(stmt)
        tones = result.scalars().all()
        return tones

    async def create_hair_tones(self, db: AsyncSession, tone: str):
        stmt = select(self.model).where(self.model.tone == tone)
        result = await db.execute(stmt)
        tone_db = result.scalars().first()

        if tone_db:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Тон волос уже существует')

        tone_new = self.model(tone=tone)
        db.add(tone_new)
        await db.commit()
        await db.refresh(tone_new)
        return tone_new

