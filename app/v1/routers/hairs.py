from fastapi import APIRouter, status, Depends

from app.v1.schemas.hairs import (HairTone, HairProduct)
from app.v1.services.hairs import (get_all_tones_hair_services, create_tone_hair_services, update_tone_hair_services,
                                   create_hair_product_services)

# Создаём маршрутизатор с префиксом и тегом
router = APIRouter(
    tags=["hairs"]
)


@router.post("/",
             response_model=HairProduct,
             status_code=status.HTTP_201_CREATED)
async def create_hair_product(hair_product: HairProduct = Depends(create_hair_product_services)):

    return hair_product


@router.get("/tones", response_model=list[HairTone], status_code=status.HTTP_200_OK)
async def get_all_tones_hair(tones_hair: list[HairTone] = Depends(get_all_tones_hair_services)):
    """
    Возвращает список всех тонов волос.
    """
    return tones_hair


@router.post("/tones",
             response_model=HairTone,
             status_code=status.HTTP_201_CREATED)
async def create_tone_hair(tones_hair: HairTone = Depends(create_tone_hair_services)):
    """
    Создает новый тон волос.
    """
    return tones_hair


@router.patch("/tones/{tone_id}",
              response_model=HairTone,
              status_code=status.HTTP_200_OK)
async def update_tone_hair(tones_hair: HairTone = Depends(update_tone_hair_services)):
    """
    Обновляет тон волос.
    """
    return tones_hair
