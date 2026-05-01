from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import String, Integer, ForeignKey, DateTime, func, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.database import Base
from app.v1.enums import OrderStatus


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment="Уникальный идентификатор позиции заказа")
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True, comment="Ссылка на заказ, к которому относится эта позиция")
    product_id: Mapped[int] = mapped_column(ForeignKey("hair_products.id"), index=True, comment="Ссылка на товар, который добавлен в позицию заказа")
    grams: Mapped[int] = mapped_column(Integer, comment="Количество граммов товара в данной позиции заказа")
    purchase_price_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), comment="Закупочная цена за 100 грамм на момент оформления позиции")
    sale_price_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), comment="цена продажи за 100 грамм на момент оформления позиции")
    total_sale_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), comment="итоговая сумма продажи именно по этой позиции: grams × sale_price_per_100g/100")
    profit: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), comment="прибыль по этой позиции: ")

    order: Mapped["Order"] = relationship("Order", back_populates="items_rel")
    product: Mapped["HairProduct"] = relationship("HairProduct")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment="Уникальный идентификатор заказа")
    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="Уникальный номер заказа в человекочитаемом формате")
    status: Mapped[str] = mapped_column(String(25), default=OrderStatus.IN_TRANSIT.value, comment="Текущий статус заказа")
    total_price: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True, comment="Общая стоимость заказа до финальных корректировок")
    final_price: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True, comment="Итоговая стоимость заказа после всех изменений и корректировок")
    profit: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True, comment="Общая прибыль по всему заказу")
    seller_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True, comment="Ссылка на пользователя-продавца, ответственного за заказ")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), comment="Дата и время создания заказа")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="Дата и время мягкого удаления заказа, если он был удален")

    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id], back_populates="orders_as_seller")
    items_rel: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    @property
    def deleted_at_formatted(self) -> str:
        """Возвращает форматированную дату удаления"""
        if self.deleted_at:
            return self.deleted_at.strftime("%d %B %Y г. в %H:%M")
        return ""
