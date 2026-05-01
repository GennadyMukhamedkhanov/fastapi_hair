from fastapi import Depends, Request
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db_depends import get_async_db
from app.common.models import HairProduct
from app.v1.conf.templates import templates
from app.v1.repositories.dependencies import get_product_repository, product_create_form, get_hair_tone_repository, \
    get_user_repository
from app.v1.repositories.helpers import get_list_status
from app.v1.repositories.products import ProductRepository
from app.v1.repositories.tones import HairToneRepository
from app.v1.repositories.users import UserRepository
from app.v1.schemas.products import ProductCreateSchema, ProductUpdateSchema, ProductStatusSchema, ProductOutSchema
from app.v1.services.tones import get_hair_tones_services
from app.v1.utils.hair import tone_and_length_sort_key


async def create_user(
        email: str,
        name: str,
        session: AsyncSession,
        users_repo: UserRepository,

) -> int:
    user_id = await users_repo.create_user(session, email, name)

    return user_id
