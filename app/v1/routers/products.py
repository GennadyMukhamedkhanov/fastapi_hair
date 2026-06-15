from fastapi import APIRouter, status, Request, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_303_SEE_OTHER

from app.common.db_depends import get_async_db
from app.v1.conf.templates import templates
from app.v1.repositories.dependencies import product_create_form, get_product_repository, get_hair_tone_repository
from app.v1.repositories.products import ProductRepository
from app.v1.repositories.tones import HairToneRepository
from app.v1.schemas.products import ProductOutSchema, ProductCreateSchema
from app.v1.services.products import update_product_services, get_product_services, \
    get_all_products_services
from app.v1.services.tones import get_hair_tones_services, create_product_tone_services

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
    #filters = data.get('filters')

    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={
            "products": products,
            #"filters": filters,
            "title": "Список товаров",
        },
    )


@router.post("/create", name="create_hair_product")
async def create_product(
        request: Request,
        data: ProductCreateSchema = Depends(product_create_form),
        session: AsyncSession = Depends(get_async_db),
        products_repo: ProductRepository = Depends(get_product_repository),
        hair_tone_repo: HairToneRepository = Depends(get_hair_tone_repository),
):
    try:
        # Создаем продукт
        product = await products_repo.create_product(session, data)
        product_valid = ProductOutSchema.model_validate(product)

        # Успех - редирект на страницу товара
        return RedirectResponse(
            url=f"/v1/hairs/{product_valid.id}?updated=1",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    except HTTPException as exc:

        tones = await get_hair_tones_services(session, hair_tone_repo)

        return templates.TemplateResponse(
            request=request,
            name="product_create.html",
            context={
                "title": "Создание товара",
                "tones": tones,
                "error_message": exc.detail,
                "form_data": {
                    "tone_id": data.tone_id,
                    "length_cm": data.length_cm,
                    "purchase_price_per_100g": data.purchase_price_per_100g,
                    "sale_price_per_100g": data.sale_price_per_100g,
                    "tax_rate": data.tax_rate,
                },
            },
            status_code=exc.status_code,
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


@router.post("/create/tone")
async def create_order_from_form(
        request: Request,
        tone_name: ProductOutSchema = Depends(create_product_tone_services)
):
    try:

        # Перенаправляем обратно на форму создания товара с сообщением об успехе
        success_message = f"Тон '{tone_name}' успешно создан!"
        return RedirectResponse(
            url=f"/v1/hairs/create?success={success_message}",
            status_code=HTTP_303_SEE_OTHER
        )
    except Exception as e:
        # В случае ошибки перенаправляем с сообщением об ошибке
        error_message = f"Ошибка при создании тона: {str(e)}"
        return RedirectResponse(
            url=f"/v1/hairs/create?tone_error={error_message}",
            status_code=HTTP_303_SEE_OTHER
        )
