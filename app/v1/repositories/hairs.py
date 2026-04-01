from sqlalchemy import select, update, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.common.models.hairs import HairTone, HairProduct, ProductStatusEnum
from app.v1.repositories.common import CommonRepository
from app.v1.schemas.hairs import UpdateHairTone, HairProductCreate


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


class HairProductRepository(CommonRepository):
    model = HairProduct

    async def create_hair_products(self, db: AsyncSession, hair_product: HairProductCreate):
        stmt = select(self.model).where(self.model.tone_id == hair_product.tone_id,
                                        self.model.length_cm == hair_product.length_cm)
        result = await db.execute(stmt)
        hair_product_db = result.scalars().first()

        if hair_product_db:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='Товар волос с таким тоном и длиной уже существует')

        hair_product_new = self.model(**hair_product.model_dump(exclude_unset=True))
        db.add(hair_product_new)
        await db.commit()
        await db.refresh(hair_product_new, ['tone'])
        return hair_product_new

    async def get_all_hair_products(self, db: AsyncSession, filters_list: list):
        if filters_list:
            stmt = (
                select(self.model)
                .where(or_(*filters_list))
                .options(selectinload(self.model.tone))
            )
        else:
            stmt = select(self.model).options(selectinload(self.model.tone))
        result = await db.execute(stmt)
        hair_products = result.scalars().all()
        return hair_products

