

from app.v1.repositories.hairs import HairTonesRepository


async def get_hair_tones_repository() -> HairTonesRepository:
    """
    Возвращает репозиторий тона волос
    """
    return HairTonesRepository()