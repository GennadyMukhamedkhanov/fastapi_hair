from decimal import Decimal
from typing import List
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import String, Integer, ForeignKey, DateTime, func, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from app.common.database import Base

class OrderStatus(str, Enum):
    """Статусы заказа"""

    IN_TRANSIT = "in_transit"        # Отправлен (в пути)
    DELIVERED = "delivered"          # Доставлен, продан
    CANCELLED = "cancelled"          # Отменён
    RETURNED = "returned"            # Возвращён


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True, comment="ID заказа")
    product_id: Mapped[int] = mapped_column(ForeignKey("hair_products.id"), index=True, comment="Товар (тон+длина)")
    grams: Mapped[int] = mapped_column(Integer, comment="Сколько грамм этого товара в заказе")
    purchase_price_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), comment="Цена закупки на момент продажи")
    sale_price_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), comment="Цена продажи за 100г")
    total_sale_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), comment="грамм * цена за 100г / 100")
    profit: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), comment="общая прибыль по строке")

    # Связи
    order: Mapped["Order"] = relationship("Order", back_populates="items_rel")
    product: Mapped["HairProduct"] = relationship("HairProduct")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment="ID заказа")
    order_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, comment="ORD-2026-00123")
    status: Mapped[OrderStatus] = mapped_column(String(20), default=OrderStatus.IN_TRANSIT, comment="in_transit/delivered/cancelled/returned")
    total_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True, comment="Сумма заказа")
    final_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True, comment="Итог продажи, заполняется при продаже для фиксации прибыли")
    profit: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True, comment="Прибыль")
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True, index=True, comment="Кто продал")
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), comment="Создан")
    deleted_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True, comment="Мягкое удаление")

    # Связи с пользователями
    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id], back_populates="orders_as_seller")
    items_rel: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order")
