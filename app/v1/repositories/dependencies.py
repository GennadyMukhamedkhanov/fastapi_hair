

from app.v1.repositories.hairs import HairTonesRepository, HairProductRepository


async def get_hair_tones_repository() -> HairTonesRepository:
    """
    Возвращает репозиторий тона волос
    """
    return HairTonesRepository()



async def get_hair_product_repository() -> HairProductRepository:
    """
    Возвращает репозиторий продукта волос
    """
    return HairProductRepository()