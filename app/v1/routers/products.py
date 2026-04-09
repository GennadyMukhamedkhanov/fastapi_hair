from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.v1.conf.templates import templates
from app.v1.repositories.tones import HairToneRepository
from app.v1.schemas.products import ProductOutSchema
from app.v1.services.products import create_product_services, update_product_services, get_product_services, \
    get_all_products_services
from app.v1.services.tones import get_hair_tones_services

# Создаём маршрутизатор с префиксом и тегом
router = APIRouter(
    tags=["hairs"]
)


@router.get("/create", response_class=HTMLResponse, name="create_hair_product_page")
async def create_product_page(
        request: Request,
        tones: HairToneRepository = Depends(get_hair_tones_services),
):
    return templates.TemplateResponse(
        request=request,
        name="product_create.html",
        context={
            "title": "Создание товара",
            "tones": tones,
            "error_message": None,
            "form_data": {},
        },
    )


@router.get("/")
async def get_all_products(request: Request, data: dict = Depends(get_all_products_services)):
    """Получить список всех товаров"""
    products = data.get('products')
    filters = data.get('filters')

    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={
            "products": products,
            "filters": filters,
            "title": "Список товаров",
        },
    )


@router.post("/create", name="create_hair_product")
async def create_product(
        request: Request,
        product: ProductOutSchema = Depends(create_product_services)

):
    return RedirectResponse(
        url=f"/v1/hairs/{product.id}?updated=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/{product_id}", name="get_hair_product")
async def get_product(
        request: Request,
        product: ProductOutSchema = Depends(get_product_services)
):
    updated = request.query_params.get("updated")

    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={
            "product": product,
            "title": "Товар",
            "success_message": "Данные успешно обновлены!" if updated else None,
        },
    )


@router.patch("/{product_id}")
async def update_product(
        product: ProductOutSchema = Depends(update_product_services)
):
    return {
        "ok": True,
        "product_id": product.id,
    }

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
