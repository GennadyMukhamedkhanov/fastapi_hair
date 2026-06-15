from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db_depends import get_async_db
from app.common.models import HairProduct
from app.v1.repositories.dependencies import get_product_repository
from app.v1.repositories.helpers import get_list_status
from app.v1.repositories.products import ProductRepository
from app.v1.schemas.products import ProductUpdateSchema, ProductStatusSchema
from app.v1.utils.hair import tone_and_length_sort_key


async def get_all_products_services(
        #status: ProductStatusSchema = Depends(),
        session: AsyncSession = Depends(get_async_db),
        products_repo: ProductRepository = Depends(get_product_repository)
):
    # status_conditions = get_list_status(
    #     status.warehouse,
    #     status.transit,
    #     status.delivered,
    #     status.return_transit
    # )

    products = await products_repo.get_all_products(session)
    products_sorted = sorted(products, key=tone_and_length_sort_key)

    return {
        "products": products_sorted,
        # "filters": {
        #     "warehouse": status.warehouse,
        #     "transit": status.transit,
        #     "delivered": status.delivered,
        #     "return_transit": status.return_transit,
        # }
    }


async def get_product_services(
        product_id: int,
        session: AsyncSession = Depends(get_async_db),
        products_repo: ProductRepository = Depends(get_product_repository)
):
    product = await products_repo.get_product(session, product_id)
    return product


async def update_product_services(
        product_id: int,
        data: ProductUpdateSchema,
        session: AsyncSession = Depends(get_async_db),
        products_repo: ProductRepository = Depends(get_product_repository),
) -> HairProduct:
    """Сервис обновления товара"""
    product = await products_repo.update_product(session, product_id, data)
    return product
