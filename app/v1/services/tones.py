from fastapi import Depends, Path, Form
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db_depends import get_async_db
from app.common.models import HairProduct
from app.v1.helpers import money
from app.v1.repositories.dependencies import get_product_repository, get_hair_tone_repository
from app.v1.repositories.helpers import get_list_status
from app.v1.repositories.products import ProductRepository
from app.v1.repositories.tones import HairToneRepository
from app.v1.schemas.products import ProductCreateSchema, ProductUpdateSchema, ProductStatusSchema, ProductOutSchema
from app.v1.utils.hair import tone_and_length_sort_key, tone_sort_key


async def get_hair_tones_services(
        session: AsyncSession = Depends(get_async_db),
        hair_tone_repo: HairToneRepository = Depends(get_hair_tone_repository),
):
    tones = await hair_tone_repo.get_all_tones(session)
    tones_sorted = sorted(tones, key=lambda t: tone_sort_key(t.tone))
    return tones_sorted


async def create_product_tone_services(
        tone_name: str = Form(...),
        session: AsyncSession = Depends(get_async_db),
        hair_tone_repo: HairToneRepository = Depends(get_hair_tone_repository),
):
    tone_name_without_spaces = tone_name.replace(" ", "")  # Убираем все пробелы
    strip_tone_name = tone_name_without_spaces.upper()

    tone = await hair_tone_repo.create_tone(session, strip_tone_name)
    return tone.tone
