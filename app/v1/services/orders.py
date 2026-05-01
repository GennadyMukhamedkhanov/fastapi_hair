from fastapi import Depends, Query
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import FormData

from app.common.config import settings
from app.common.db_depends import get_async_db
from app.common.models import User, Order
from app.common.services.security import get_user_data_from_token
from app.v1.enums import OrderStatus
from app.v1.repositories.dependencies import get_product_repository, get_order_repository
from app.v1.repositories.orders import OrderRepository
from app.v1.repositories.products import ProductRepository
from app.v1.schemas.orders import OrderItemCreate, OrderCreateSchema, FilterStatusSchema
from app.v1.utils.hair import tone_and_length_sort_key
from fastapi import Request


async def get_orders_page_service(
        request: Request,
        my_only: bool = Query(False),
        filters: FilterStatusSchema = Depends(),
        session: AsyncSession = Depends(get_async_db),
        order_repo: "OrderRepository" = Depends(get_order_repository),

):
    filters_list = get_list_filters(filters.transit,
                                    filters.delivered,
                                    filters.return_transit,
                                    filters.returned_on_warehouse,
                                    filters.deleted
                                    )

    # ✅ Получаем токен из cookie
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user_data = get_user_data_from_token(token)
    user_id = user_data.get("user_id")
    seller_id = user_id if my_only else None

    orders = await order_repo.get_orders(
        session=session,
        seller_id=seller_id,
        filters=filters_list
    )

    return {
        "orders": orders,
        "my_only": my_only,
    }


def get_list_filters(transit, delivered, return_transit, returned_on_warehouse, deleted):
    filters = []

    if transit:
        filters.append(Order.status == OrderStatus.IN_TRANSIT.value)
    if delivered:
        filters.append(Order.status == OrderStatus.DELIVERED.value)
    if return_transit:
        filters.append(Order.status == OrderStatus.RETURN_TRANSIT.value)
    if returned_on_warehouse:
        filters.append(Order.status == OrderStatus.RETURNED_ON_WAREHOUSE.value)
    if deleted:
        filters.append(Order.status == OrderStatus.DELETED.value)

    return filters


async def get_create_order_page_service(
        session: AsyncSession = Depends(get_async_db),
        products_repo: ProductRepository = Depends(get_product_repository),
):
    products = await products_repo.get_products_available_for_order(session)
    products_sorted = sorted(products, key=tone_and_length_sort_key)

    return {
        "products": products_sorted,
    }


async def create_order_from_form_service(
        form: FormData,
        user_id: int,
        session: AsyncSession,
        order_repo: "OrderRepository",
        user_name: str,
        delivery_service: str
):
    items: list[OrderItemCreate] = []

    for key, value in form.items():
        if not key.startswith("product_"):
            continue

        if not value:
            continue

        grams = int(value)
        if grams <= 0:
            continue

        try:
            product_id = int(key.replace("product_", ""))
        except ValueError:
            continue

        items.append(OrderItemCreate(product_id=product_id, grams=grams))

    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не выбрано ни одного товара для заказа",
        )

    order_data = OrderCreateSchema(
        items=items,
        seller_id=user_id,
    )

    return await order_repo.create_order(session=session,
                                         order_data=order_data,
                                         user_name=user_name,
                                         delivery_service=delivery_service)


async def delete_order_service(
        order_id: int,
        session: AsyncSession = Depends(get_async_db),
        order_repo: "OrderRepository" = Depends(get_order_repository)
):
    order = await order_repo.get_order_by_id_with_lock(session=session, order_id=order_id)

    if order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if order.deleted_at is not None:
        raise HTTPException(status_code=400, detail="Заказ уже удален")

    if order.status != OrderStatus.IN_TRANSIT.value:
        raise HTTPException(status_code=400, detail="Тольза заказы со статусом 'В пути' могут быть удалены")

    return await order_repo.soft_delete_order(session=session, order=order)