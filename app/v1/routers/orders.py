from decimal import Decimal

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import settings
from app.common.db_depends import get_async_db
from app.common.models import Order
from app.common.services.security import get_user_data_from_token
# from app.v1.services.orders import OrderService
from app.v1.conf.templates import templates
from app.v1.enums import OrderStatus
from app.v1.repositories.dependencies import get_order_repository, get_product_repository
from app.v1.repositories.orders import OrderRepository
from app.v1.repositories.products import ProductRepository
from app.v1.schemas.orders import StatusUpdateSchema
from app.v1.services.orders import get_create_order_page_service, \
    create_order_from_form_service, get_orders_page_service, delete_order_service

router = APIRouter(
    tags=["orders"]
)


@router.get("/", response_class=HTMLResponse, name="create_hair_product_page")
async def get_main_page_orders(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="orders.html"
    )


@router.get("/list", name="get_orders_page")
async def get_orders_page(
        request: Request,
        data: dict = Depends(get_orders_page_service),
):
    return templates.TemplateResponse(
        request=request,
        name="orders_list.html",
        context={
            "title": "Список заказов",
            "orders": data["orders"],
            "my_only": data["my_only"],
        },
    )


@router.get("/create")
async def get_create_order_page(
        request: Request,
        data: dict = Depends(get_create_order_page_service),
):
    return templates.TemplateResponse(
        request=request,
        name="order_create.html",
        context={
            "title": "Создание заказа",
            "products": data["products"],
            "gram_options": [0, 50, 100, 150, 200, 250, 300],
            "delivery service": ["Авито", "Яндекс", "Почта", "СДЕК", "5Post", "Иное"],
        },
    )


@router.post("/create")
async def create_order_from_form(
        request: Request,
        session: AsyncSession = Depends(get_async_db),
        order_repo: "OrderRepository" = Depends(get_order_repository),
        delivery_service: str = Form(...),
):
    form = await request.form()

    # ✅ Получаем токен из cookie
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user_data = get_user_data_from_token(token)
    user_id = user_data.get("user_id")
    user_name = user_data.get("name")

    order = await create_order_from_form_service(
        form=form,
        user_id=user_id,
        session=session,
        order_repo=order_repo,
        user_name=user_name,
        delivery_service=delivery_service

    )

    redirect_url = request.url_for("get_order_detail_page", order_id=order.id)
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


# @router.get("/delete/{order_id}")
# async def delete_order(request: Request,
#                        order: Order = Depends(delete_order_service)):
#
#     redirect_url = request.url_for("get_order_detail_page", order_id=order.id)
#     return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
@router.get("/delete/{order_id}")
async def delete_order(
    request: Request,
    order_id: int,
    session: AsyncSession = Depends(get_async_db),
    order_repo: "OrderRepository" = Depends(get_order_repository)
):
    try:
        order = await delete_order_service(order_id, session, order_repo)
        redirect_url = request.url_for("get_order_detail_page", order_id=order.id)
        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="order_deleted", value="true", max_age=5, path="/")
        return response
    except HTTPException as e:
        redirect_url = request.url_for("get_order_detail_page", order_id=order_id)
        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="delete_error", value=e.detail, max_age=5, path="/")
        return response

@router.get("/{order_id}", name="get_order_detail_page")
async def get_order_detail_page(
        order_id: int,
        request: Request,
        session: AsyncSession = Depends(get_async_db),
        order_repo: "OrderRepository" = Depends(get_order_repository),
):
    order = await order_repo.get_order_by_id(session=session, order_id=order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    order.created_at_formatted = order.created_at.strftime("%H:%M %d-%m- %Y")

    for item in order.items_rel:
        weight_in_100g = Decimal(str(item.grams)) / Decimal('100')
        item.purchase_total = item.purchase_price_per_100g * weight_in_100g
        item.sale_total = item.sale_price_per_100g * weight_in_100g
        item.profit_calculated = item.sale_total - item.purchase_total

    return templates.TemplateResponse(
        request=request,
        name="order_detail.html",
        context={
            "title": f"Заказ {order.order_number}",
            "order": order,
        },
    )


@router.patch("/{order_id}/status")
async def update_order_status(
        order_id: int,
        request: Request,
        update_data: StatusUpdateSchema,
        session: AsyncSession = Depends(get_async_db),
        orders_repo: OrderRepository = Depends(get_order_repository),
        products_repo: ProductRepository = Depends(get_product_repository)

):
    new_status = update_data.status
    sale_prices = update_data.sale_prices
    """Обновление статуса заказа"""

    if new_status not in ["transit", "delivered", "return_transit", "returned_on_warehouse"]:
        raise HTTPException(status_code=400, detail="Неверный статус")

    # Получаем заказ
    order = await orders_repo.get_order_by_id(session, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    # ✅ Получаем токен из cookie
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user_data = get_user_data_from_token(token)
    user_id = user_data.get("user_id")
    # Проверяем права (только продавец может менять статус)
    if order.seller_id != user_id:
        raise HTTPException(status_code=403, detail="Нет прав для изменения статуса")

    if new_status == OrderStatus.DELIVERED.value and order.status == OrderStatus.IN_TRANSIT.value:
        order = await orders_repo.set_sale_prices_on_delivery(
            session=session,
            order_id=order_id,
            sale_prices=sale_prices,
        )

    if new_status == OrderStatus.RETURN_TRANSIT.value and order.status == OrderStatus.IN_TRANSIT.value:
        order.status = OrderStatus.RETURN_TRANSIT.value
        await session.commit()

    if new_status == OrderStatus.RETURNED_ON_WAREHOUSE.value and (
            order.status == OrderStatus.RETURN_TRANSIT.value or
            order.status == OrderStatus.IN_TRANSIT.value
    ):

        try:
            # Восстанавливаем остатки товаров

            for item in order.items_rel:
                product = await products_repo.get_product(session, item.product_id)

                product.stock_grams += item.grams
                session.add(product)  # Явно добавляем в сессию

                item.purchase_price_per_100g = Decimal("0.00")
                item.sale_price_per_100g = Decimal("0.00")
                item.total_sale_price = Decimal("0.00")
                item.profit = Decimal("0.00")
                session.add(item)

            # Обнуляем финансовые показатели
            order.total_price = Decimal("0.00")
            order.final_price = Decimal("0.00")
            order.profit = Decimal("0.00")

            # Обновляем статус заказа
            order.status = OrderStatus.RETURNED_ON_WAREHOUSE.value

            # Явно добавляем заказ в сессию
            session.add(order)

            # Принудительно сбрасываем все изменения
            await session.flush()
            await session.commit()

            return {
                "success": True,
                "status": new_status,
                "order_id": order.id,
                "order_number": order.order_number,
                "total_price": str(order.total_price),
                "final_price": str(order.final_price),
                "profit": str(order.profit),
                "message": f"Заказ #{order.order_number} возвращен на склад, финансы обнулены"
            }


        except Exception as e:

            await session.rollback()

            print(f"Ошибка при возврате заказа: {e}")

            raise HTTPException(

                status_code=500,

                detail=f"Ошибка при возврате заказа: {str(e)}"

            )

    return {
        "success": True,
        "status": new_status,
        "order_id": order.id,
        "order_number": order.order_number,
        "message": f"Статус заказа #{order.order_number} обновлен на '{new_status}'"
    }
