from sqlalchemy import Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from app.common.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True,
                                    comment="Уникальный ID пользователя (автоинкремент)")
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True,
                                          comment="Логин продавца (уникальный, макс. 50 символов)")
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True,
                                       comment="Email продавца для уведомлений (уникальный, макс. 100 символов)")
    hashed_password: Mapped[str] = mapped_column(String, comment="Захэшированный пароль (bcrypt) для аутентификации")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False,
                                           comment="Флаг главного администратора (True=супер-админ с полными правами)")
    phone: Mapped[str] = mapped_column(String(20), nullable=True,
                                       comment="Телефон продавца для внутренних коммуникаций")
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(),
                                                 comment="Дата и время регистрации продавца в системе")



    orders_as_seller: Mapped[List["Order"]] = relationship("Order", foreign_keys="Order.seller_id",
                                                           back_populates="seller")