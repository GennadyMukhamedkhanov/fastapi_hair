from fastapi import Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.common.models import Order
from app.v1.enums import OrderStatus
from app.v1.repositories.dependencies import get_order_repository
from app.v1.repositories.helpers import generate_order_number
from app.v1.repositories.orders import OrderRepository
from app.v1.schemas.orders import OrderCreateSchema, OrderStatusUpdateSchema

#
# class OrderService:
#     def __init__(self, repo: OrderRepository):
#         self.repo = repo
#         self.allowed_transitions = {
#             OrderStatus.IN_TRANSIT.value: {OrderStatus.DELIVERED.value, OrderStatus.RETURN_TRANSIT.value},
#             OrderStatus.RETURN_TRANSIT.value: {OrderStatus.RETURNED_ON_WAREHOUSE.value},
#         }
#
#     async def create_order(self, db: AsyncSession, data: OrderCreateSchema, seller_id: int | None = None) -> Order:
#         """Сервис создания заказа с полной проверкой"""
#         if not data.items:
#             raise HTTPException(status_code=400, detail="Order must contain items")
#
#         order_number = await generate_order_number(db)
#         order_data = {
#             "order_number": order_number,
#             "status": OrderStatus.IN_TRANSIT.value,
#             "seller_id": seller_id,
#             "items": [{"product_id": item.product_id, "grams": item.grams} for item in data.items]
#         }
#
#         return await self.repo.create_order(db, order_data)
#
#     async def change_status(self, db: AsyncSession, order_id: int, status_data: OrderStatusUpdateSchema) -> Order:
#         """Сервис смены статуса с бизнес-логикой"""
#         order = await self.repo.get_order_by_id(db, order_id)
#
#         if status_data.status.value not in self.allowed_transitions.get(order.status, set()):
#             raise HTTPException(status_code=400,
#                                 detail=f"Invalid transition: {order.status} → {status_data.status.value}")
#
#         # Бизнес-логика по статусам
#         if status_data.status == OrderStatus.DELIVERED:
#             order.final_price = status_data.final_price or order.total_price
#             # Списываем резерв
#             for item in order.items_rel:
#                 await self.repo.update_product_stock(db, item.product_id, -item.grams)
#
#         elif status_data.status == OrderStatus.RETURNED_ON_WAREHOUSE:
#             # Возвращаем на склад
#             for item in order.items_rel:
#                 await self.repo.update_product_stock(db, item.product_id, item.grams)
#             order.final_price = Decimal("0")
#             order.profit = Decimal("0")
#
#         order.status = status_data.status.value
#         await db.commit()
#         await db.refresh(order)
#         return order
