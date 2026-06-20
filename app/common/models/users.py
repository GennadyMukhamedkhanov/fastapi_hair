from datetime import datetime
from typing import List, Union

from sqlalchemy import Integer, String, DateTime, Boolean
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    orders_as_seller: Mapped[List["Order"]] = relationship(
        "Order",
        foreign_keys="Order.seller_id",
        back_populates="seller"
    )
    wallet: Mapped[Union["Wallet", None]] = relationship("Wallet", uselist=False, back_populates="user")
    transactions: Mapped[List["WalletTransaction"]] = relationship("WalletTransaction", back_populates="user")





