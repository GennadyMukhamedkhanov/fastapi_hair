from sqlalchemy import String, Float, Integer, ForeignKey, Boolean, DateTime, func, CheckConstraint, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from decimal import Decimal
from typing import List
from app.database import Base
from datetime import datetime


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный ID продажи"
    )

    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id"),
        unique=True,
        comment="ID позиции заказа (уникально - 1 позиция = 1 продажа)"
    )

    seller_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        comment="ID продавца, зафиксировавшего продажу"
    )

    sale_date: Mapped[DateTime] = mapped_column(
        DateTime,
        default=func.now(),
        comment="Дата фиксации продажи"
    )

    final_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        comment="Итоговая цена продажи с учетом налога"
    )

    profit: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        comment="Прибыль = final_price - (закупка × количество × (1+налог))"
    )

    deleted_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=True,
        comment="Мягкое удаление продажи (NULL=активна)"
    )

    # Связь: продавец этой продажи
    seller: Mapped["User"] = relationship(back_populates="sales")

    # Связь: позиция заказа этой продажи
    order_item: Mapped["OrderItem"] = relationship(back_populates="sale")
