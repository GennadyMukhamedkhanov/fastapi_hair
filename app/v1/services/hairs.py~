from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db_depends import get_async_db
from app.v1.repositories.dependencies import get_hair_tones_repository
from app.v1.repositories.hairs import HairTonesRepository
from app.v1.schemas.hairs import CreateHairTone, UpdateHairTone
from app.v1.utils.hair import tone_sort_key


async def get_all_tones_hair_services(db: AsyncSession = Depends(get_async_db),
                                      hair_tones_repo: HairTonesRepository = Depends(get_hair_tones_repository)):
    tones = await hair_tones_repo.get_all_hair_tones(db)
    tones_sorted = sorted(tones, key=lambda x: tone_sort_key(x.tone))
    return tones_sorted


async def create_tone_hair_services(tone: CreateHairTone,
                                    db: AsyncSession = Depends(get_async_db),
                                    hair_tones_repo: HairTonesRepository = Depends(get_hair_tones_repository)):
    tone = await hair_tones_repo.create_hair_tones(db, tone.tone)
    return tone


async def update_tone_hair_services(tone_id: int,
                                    tone: UpdateHairTone,
                                    db: AsyncSession = Depends(get_async_db),
                                    hair_tones_repo: HairTonesRepository = Depends(get_hair_tones_repository)):
    tone = await hair_tones_repo.update_hair_tones(db, tone_id, tone)
    return tone
