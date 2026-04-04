from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db_depends import get_async_db
from app.v1.schemas.orders import OrderOutSchema, OrderCreateSchema, OrderStatusUpdateSchema
# from app.v1.services.orders import OrderService
#
# router = APIRouter(
#     tags=["orders"]
# )
#
#
# @router.post("/", response_model=OrderOutSchema, status_code=201)
# async def create_order(
#         payload: OrderCreateSchema,
#         session: AsyncSession = Depends(get_async_db),
#         service: OrderService = Depends()
# ):
#     """Создать заказ"""
#     return await service.create_order(session, payload)
#
#
# @router.patch("/{order_id}/status", response_model=OrderOutSchema)
# async def change_order_status(
#         order_id: int,
#         payload: OrderStatusUpdateSchema,
#         session: AsyncSession = Depends(get_async_db),
#         service: OrderService = Depends()
# ):
#     """Сменить статус заказа"""
#     return await service.change_status(session, order_id, payload)
