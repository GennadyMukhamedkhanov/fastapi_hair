from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.common.models import Order, OrderItem
from app.common.models.hairs import HairProduct
from app.v1.helpers import calc_total_price, calc_profit, money
from app.v1.repositories.common import CommonRepository

#
# class OrderRepository(CommonRepository):
#     model = Order
#
#     async def create_order(self, db: AsyncSession, order_data: dict) -> Order:
#         """Создает заказ с проверкой остатков"""
#         # SELECT FOR UPDATE для блокировки товаров
#         product_ids = [item["product_id"] for item in order_data["items"]]
#         stmt = select(HairProduct).where(HairProduct.id.in_(product_ids))
#         result = await db.execute(stmt.with_for_update())
#         products = {p.id: p for p in result.scalars().all()}
#
#         # Проверяем остатки
#         total_price = Decimal("0.00")
#         total_profit = Decimal("0.00")
#
#         for item_data in order_data["items"]:
#             product = products[item_data["product_id"]]
#             grams = item_data["grams"]
#
#             available = product.stock_grams - product.reserved_grams
#             if available < grams:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"Insufficient stock for product {product.id}: {available}g available"
#                 )
#
#             # Резервируем
#             product.reserved_grams += grams
#             line_total = calc_total_price(grams, product.sale_price_per_100g)
#             line_profit = calc_profit(grams, product.sale_price_per_100g,
#                                       product.purchase_price_per_100g, product.tax_rate)
#
#             total_price += line_total
#             total_profit += line_profit
#
#             # Создаем OrderItem
#             order_item = OrderItem(
#                 order_id=order_data["id"],
#                 product_id=product.id,
#                 grams=grams,
#                 purchase_price_per_100g=product.purchase_price_per_100g,
#                 sale_price_per_100g=product.sale_price_per_100g,
#                 total_sale_price=line_total,
#                 profit=line_profit
#             )
#             db.add(order_item)
#
#         # Финализируем заказ
#         order = self.model(
#             **order_data,
#             total_price=money(total_price),
#             profit=money(total_profit)
#         )
#         db.add(order)
#         await db.commit()
#         await db.refresh(order)
#         return order
#
#     async def get_order_by_id(self, db: AsyncSession, order_id: int) -> Order:
#         """Получает заказ по ID вместе с позициями и товарами"""
#         stmt = (
#             select(Order)
#             .where(Order.id == order_id)
#             .options(
#                 selectinload(Order.items_rel).selectinload(OrderItem.product)
#             )
#         )
#         result = await db.execute(stmt)
#         order = result.scalar_one_or_none()
#
#         if not order:
#             raise HTTPException(status_code=404, detail="Order not found")
#
#         return order
#
#     async def update_product_stock(self, db: AsyncSession, product_id: int, delta_grams: int) -> HairProduct:
#         """Обновляет складской остаток и резерв товара"""
#         stmt = select(HairProduct).where(HairProduct.id == product_id).with_for_update()
#         result = await db.execute(stmt)
#         product = result.scalar_one_or_none()
#
#         if not product:
#             raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
#
#         new_stock = product.stock_grams + delta_grams
#         if new_stock < 0:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Insufficient stock for product {product.id}"
#             )
#
#         product.stock_grams = new_stock
#
#         if delta_grams < 0:
#             reserved_after_write_off = product.reserved_grams - abs(delta_grams)
#             product.reserved_grams = max(0, reserved_after_write_off)
#
#         await db.flush()
#         return product
