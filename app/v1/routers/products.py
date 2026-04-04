from fastapi import APIRouter, Depends, status

from app.v1.schemas.products import ProductOutSchema
from app.v1.services.products import create_product_services, update_product_services, get_product_services, \
    get_all_products_services

# Создаём маршрутизатор с префиксом и тегом
router = APIRouter(
    tags=["hairs"]
)


@router.get("/", response_model=list[ProductOutSchema])
async def get_all_products(products: list[ProductOutSchema] = Depends(get_all_products_services)):
    """Получить список всех товаров"""
    return products

@router.get("/{product_id}", response_model=ProductOutSchema)
async def get_product(product: ProductOutSchema = Depends(get_product_services)):
    """Получить товар по id"""
    return product


@router.post("/", response_model=ProductOutSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductOutSchema = Depends(create_product_services)):
    """
    Создать новый товар.
    """

    return product


@router.patch("/{product_id}", response_model=ProductOutSchema)
async def update_product(product: ProductOutSchema = Depends(update_product_services)):
    """Обновить товар"""
    return product

#
# @router.get("/", response_model=ProductListResponse)
# async def list_products(
#         session: AsyncSession = Depends(get_async_db),
#         pagination: PageParams = Depends(),
#         filters: ProductFilterParamsSchema = Depends(),
#         sort: SortParams = Depends(),
#         repo: ProductRepository = Depends(get_product_repository)
# ):
#     """Список товаров с фильтрацией/пагинацией"""
#     data = await repo.get_products_list(session, pagination.page, pagination.page_size, filters, sort)
#     data["items"] = [ProductOutSchema.model_validate(p) for p in data["items"]]
#     return ProductListResponse(**data)
