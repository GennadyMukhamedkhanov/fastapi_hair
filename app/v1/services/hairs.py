from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db_depends import get_async_db
from app.common.models import HairProduct
from app.v1.repositories.dependencies import get_hair_tones_repository, get_hair_product_repository
from app.v1.repositories.hairs import HairTonesRepository, HairProductRepository
from app.v1.schemas.hairs import CreateHairTone, UpdateHairTone, HairProductCreate, ProductStatusFilter
from app.v1.utils.hair import tone_sort_key, tone_and_length_sort_key
from typing import Annotated


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


async def create_hair_product_services(hair_product: HairProductCreate,
                                       db: AsyncSession = Depends(get_async_db),
                                       hair_product_repo: HairProductRepository = Depends(get_hair_product_repository)):
    hair_products = await hair_product_repo.create_hair_products(db, hair_product)
    return hair_products


# Todo-------------------------------------
async def get_all_hair_products_services(
        filters: Annotated[ProductStatusFilter, Depends()],
        db: AsyncSession = Depends(get_async_db),
        hair_product_repo: HairProductRepository = Depends(get_hair_product_repository)):
    # Формируем список фильтров
    filters_list = get_list_filters(filters.warehouse,
                                    filters.transit,
                                    filters.sold,
                                    filters.return_transit,
                                    )

    hair_products = await hair_product_repo.get_all_hair_products(db, filters_list)
    sorted_tones = sorted(hair_products, key=lambda x: tone_and_length_sort_key(x))
    return sorted_tones


def get_list_filters(warehouse, transit, sold, return_transit):
    filters = []

    if warehouse:
        filters.append(HairProduct.status == "warehouse")
    if transit:
        filters.append(HairProduct.status == "transit")
    if sold:
        filters.append(HairProduct.status == "sold")
    if return_transit:
        filters.append(HairProduct.status == "return_transit")
    return filters



