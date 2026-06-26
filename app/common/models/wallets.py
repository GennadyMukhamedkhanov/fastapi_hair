# app/v1/models/wallet.py
from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from sqlalchemy import (
    Numeric, String, Text, ForeignKey,
    DateTime, Index, CheckConstraint, Integer
)
from sqlalchemy import func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.database import Base
from app.v1.enums import TransactionType


class Wallet(Base):
    """
    Кошелек пользователя - каждый пользователь имеет свой уникальный кошелек
    """
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Связь с пользователем (уникальный ключ - один пользователь = один кошелек)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=text("TIMEZONE('Europe/Moscow', NOW())"),
        onupdate=text("TIMEZONE('Europe/Moscow', NOW())"),
        nullable=False
    )

    # Связи
    user: Mapped["User"] = relationship(
        "User",
        back_populates="wallet"
    )

    transactions: Mapped[List["WalletTransaction"]] = relationship(
        "WalletTransaction",
        back_populates="wallet",
        cascade="all, delete-orphan",
        order_by="WalletTransaction.created_at.desc()"
    )

    # =====================================================
    #  МЕТОДЫ ДЛЯ РАБОТЫ С БАЛАНСОМ
    # =====================================================
    def add_balance(self, amount: Decimal) -> None:
        """Увеличить баланс кошелька"""
        if amount < 0:
            raise ValueError("Сумма для добавления не может быть отрицательной")
        self.balance += amount

    def subtract_balance(self, amount: Decimal) -> None:
        """Уменьшить баланс кошелька"""
        if amount < 0:
            raise ValueError("Сумма для списания не может быть отрицательной")
        if self.balance < amount:
            raise ValueError(
                f"Недостаточно средств. Баланс: {self.balance:.2f}, запрошено: {amount:.2f}"
            )
        self.balance -= amount

    def set_balance(self, amount: Decimal) -> None:
        """Установить конкретное значение баланса"""
        if amount < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self.balance = amount

    def has_enough_funds(self, amount: Decimal) -> bool:
        """Проверить, достаточно ли средств на балансе"""
        return self.balance >= amount

    @property
    def balance_display(self) -> str:
        """Форматированное отображение баланса"""
        return f"{self.balance:.2f} ₽"

    # =====================================================
    # ОГРАНИЧЕНИЯ ТАБЛИЦЫ
    # =====================================================
    __table_args__ = (
        CheckConstraint("balance >= 0", name="balance_non_negative"),
        Index("ix_wallets_user_balance", "user_id", "balance"),
    )

    # =====================================================
    #  МАГИЧЕСКИЕ МЕТОДЫ
    # =====================================================
    def __repr__(self) -> str:
        return f"<Wallet(id={self.id}, user_id={self.user_id}, balance={self.balance})>"

    def __str__(self) -> str:
        return f"Кошелек пользователя #{self.user_id} (баланс: {self.balance:.2f} ₽)"


class WalletTransaction(Base):
    """
    Транзакция кошелька - каждая операция с деньгами
    """
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )


    # ТИП ТРАНЗАКЦИИ
    transaction_type: Mapped[TransactionType] = mapped_column(
        String(20),
        nullable=False,
        default=TransactionType.SALE,
        index=True
    )

    # Сумма продажи
    sale_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Себестоимость товара
    cost_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Прибыль с продажи
    profit_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    ##  СУММА ТРАНЗАКЦИИ (ДЛЯ УНИФИКАЦИИ)
    # ✅ Добавлено для всех типов транзакций
    # Особенно необходимо когда выводим средства или добавляем,
    # и не используем sale_amount, cost_amount и profit_amount
    amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Сумма транзакции"
    )

    # ОПИСАНИЕ / КОММЕНТАРИЙ
    description: Mapped[str | None] = mapped_column(Text, nullable=True)



    # ВРЕМЕННЫЕ МЕТКИ
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=text("TIMEZONE('Europe/Moscow', NOW())"),
        nullable=False,
        index=True
    )

    # МЯГКОЕ УДАЛЕНИЕ
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
        server_default="false"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # СВЯЗИ
    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="transactions")
    user: Mapped["User"] = relationship("User", back_populates="transactions")

    # =====================================================
    # ОГРАНИЧЕНИЯ ТАБЛИЦЫ
    # =====================================================
    __table_args__ = (
        CheckConstraint(
            "profit_amount IS NULL OR profit_amount >= 0",
            name="profit_non_negative"
        ),
        CheckConstraint(
            "sale_amount IS NULL OR sale_amount >= 0",
            name="sale_non_negative"
        ),
        CheckConstraint(
            "cost_amount IS NULL OR cost_amount >= 0",
            name="cost_non_negative"
        ),
        CheckConstraint(
            "amount IS NULL OR amount >= 0",
            name="amount_non_negative"
        ),
        Index("ix_transactions_created_deleted", "created_at", "is_deleted"),
        Index("ix_transactions_type_created", "transaction_type", "created_at"),
        Index("ix_transactions_user_created", "user_id", "created_at"),
    )

    # =====================================================
    # МЕТОДЫ ДЛЯ МЯГКОГО УДАЛЕНИЯ
    # =====================================================
    def soft_delete(self) -> None:
        """Мягкое удаление транзакции"""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Восстановление транзакции"""
        self.is_deleted = False
        self.deleted_at = None

    def __str__(self) -> str:
        if self.transaction_type == TransactionType.SALE and self.sale_amount:
            return f"Продажа #{self.id}: {self.sale_amount:.2f} ₽"
        elif self.amount:
            return f"{self.transaction_type.value.capitalize()} #{self.id}: {self.amount:.2f} ₽"
        return f"Транзакция #{self.id} ({self.transaction_type.value})"
