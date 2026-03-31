from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.common.models.hairs import HairTone
from app.v1.repositories.common import CommonRepository
from app.v1.schemas.hairs import UpdateHairTone


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

    async def update_hair_tones(self, db: AsyncSession, tone_id: int, tone: UpdateHairTone):

        update_tone = tone.model_dump(exclude_unset=True)
        if not update_tone:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Нет данных для обновления')

        stmt = update(self.model).where(self.model.id == tone_id).values(**update_tone).returning(self.model)
        result = await db.execute(stmt)
        tone_db = result.scalars().first()
        if not tone_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Тон волос не найден')
        await db.commit()
        return tone_db
