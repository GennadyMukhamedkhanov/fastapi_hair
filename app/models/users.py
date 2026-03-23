from typing import List

from sqlalchemy import String, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from sqlalchemy import Integer, String, DECIMAL, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List
from app.database import Base
from app.models.orders import Order


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный ID пользователя (автоинкремент)"
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        comment="Логин продавца (уникальный, макс. 50 символов)"
    )

    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        comment="Email продавца для уведомлений (уникальный, макс. 100 символов)"
    )

    hashed_password: Mapped[str] = mapped_column(
        String,
        comment="Захэшированный пароль (bcrypt) для аутентификации"
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Флаг главного администратора (True=супер-админ с полными правами)"
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
        comment="Телефон продавца для внутренних коммуникаций"
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=func.now(),
        comment="Дата и время регистрации продавца в системе"
    )

    # ✅ Связи с правильными back_populates
    orders_as_buyer: Mapped[List["Order"]] = relationship(
        "Order",
        foreign_keys=[Order.buyer_id],
        back_populates="buyer"
    )

    orders_as_shipper: Mapped[List["Order"]] = relationship(
        "Order",
        foreign_keys=[Order.shipper_id],
        back_populates="shipper"
    )

    # ✅ Связь: продажи, зафиксированные этим продавцом
    sales: Mapped[List["Sale"]] = relationship(
        "Sale",
        back_populates="seller",
        cascade="all, delete-orphan"  # опционально: при удалении продавца удалить и продажи
    )

