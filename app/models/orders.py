from decimal import Decimal
from typing import List

from sqlalchemy import String, Integer, ForeignKey, DateTime, func, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный ID заказа (внутренний)"
    )

    order_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        comment="Уникальный номер заказа для поиска (ORD-2026-00123)"
    )

    buyer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        comment="ID продавца, создавшего заказ (nullable - внутренние перемещения)"
    )

    buyer_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
        comment="Телефон клиента (nullable - пока без публичных покупателей)"
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="new",
        index=True,
        comment="Статус заказа: new/confirmed/in_transit/delivered/cancelled"
    )

    total_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=True,
        comment="Общая сумма заказа с учетом налога"
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=func.now(),
        comment="Дата создания заказа"
    )

    shipper_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        comment="ID продавца-отправителя (кто отправил товар)"
    )

    deleted_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=True,
        comment="Мягкое удаление заказа (NULL=активен)"
    )

    # ✅ Связи с двусторонним back_populates
    buyer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[buyer_id],
        back_populates="orders_as_buyer"
    )

    shipper: Mapped["User"] = relationship(
        "User",
        foreign_keys=[shipper_id],
        back_populates="orders_as_shipper"
    )

    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Уникальный ID позиции в заказе"
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        comment="ID заказа (ForeignKey)"
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("hair_products.id"),
        comment="ID товара (ForeignKey на hair_products)"
    )

    grams: Mapped[int] = mapped_column(
        Integer,
        comment="Количество грамм (50, 100, 150... кратно 50г)"
    )

    # Связь: заказ этой позиции
    order: Mapped["Order"] = relationship(back_populates="items")

    # Связь: товар этой позиции
    product: Mapped["HairProduct"] = relationship(back_populates="order_items")
