from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import select, desc, func, case, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.models import Order, OrderItem, Wallet, WalletTransaction
from app.common.models.hairs import HairProduct, HairTone
from app.v1.enums import ProductStatusEnum, OrderStatus, TransactionType
from app.v1.repositories.common import CommonRepository
from app.v1.schemas.orders import OrderCreateSchema


class TransactionRepository(CommonRepository):
    model = WalletTransaction

    async def get_all_transactions(
            self,
            session: AsyncSession

    ) -> list[WalletTransaction]:
        stmt = (
            select(self.model)
            .options(selectinload(self.model.user))
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create_transaction(
            self,
            session: AsyncSession,
            wallet_id: int,
            user_id: int,
            transaction_type: str,
            sale_amount: Decimal,
            cost_amount: Decimal,
            profit_amount: Decimal,
            amount: Decimal,
            description: str

    ) -> None:
        transaction = self.model(
            wallet_id=wallet_id,
            user_id=user_id,
            transaction_type=transaction_type,
            sale_amount=sale_amount,
            cost_amount=cost_amount,
            profit_amount=profit_amount,
            amount=amount,
            description=description
        )

        session.add(transaction)
        await session.flush()

    async def get_transaction_by_description(
            self,
            session: AsyncSession,
            order_number: str
    ) -> WalletTransaction:
        stmt = select(self.model).where(self.model.description == order_number)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_purchase_transaction_repository(
            self,
            session: AsyncSession,
            amount: Decimal,
            description: str,
            user_id: int,
            wallet_id: int,
    ) -> bool:
        try:
            stmt = select(Wallet).where(
                Wallet.id == wallet_id,
                Wallet.user_id == user_id
            )
            result = await session.execute(stmt)
            wallet = result.scalar_one_or_none()

            if wallet is None:
                raise HTTPException(status_code=404, detail="Кошелек не найден")

            if amount <= 0:
                raise HTTPException(status_code=400, detail="Сумма должна быть больше 0")

            wallet.subtract_balance(amount)

            transaction = self.model(
                wallet_id=wallet_id,
                user_id=user_id,
                transaction_type=TransactionType.PURCHASE.value,
                amount=amount,
                description=description,
            )
            session.add(transaction)

            await session.commit()
            await session.refresh(transaction)
            return True

        except Exception:
            await session.rollback()
            raise

    async def create_transfer_transaction_repository(
            self,
            session: AsyncSession,
            amount: Decimal,
            description: str,
            user_id: int,
            wallet_id: int,
    ) -> bool:

        stmt = select(Wallet).where(
            Wallet.id == wallet_id,
            Wallet.user_id == user_id
        )
        result = await session.execute(stmt)
        wallet = result.scalar_one_or_none()

        if wallet is None:
            raise HTTPException(status_code=404, detail="Кошелек не найден")

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Сумма должна быть больше 0")

        wallet.subtract_balance(amount)

        transaction = self.model(
            wallet_id=wallet_id,
            user_id=user_id,
            transaction_type=TransactionType.TRANSFER.value,
            amount=amount,
            description=description,
        )
        session.add(transaction)

        return True

    async def create_deposit_transaction_repository(
            self,
            session: AsyncSession,
            amount: Decimal,
            description: str,
            user_id: int,
            wallet_id: int,
    ) -> bool:

        stmt = select(Wallet).where(
            Wallet.id == wallet_id,
            Wallet.user_id == user_id
        )
        result = await session.execute(stmt)
        wallet = result.scalar_one_or_none()

        if wallet is None:
            raise HTTPException(status_code=404, detail="Кошелек не найден")

        wallet.add_balance(amount)

        transaction = self.model(
            wallet_id=wallet_id,
            user_id=user_id,
            transaction_type=TransactionType.DEPOSIT.value,
            amount=amount,
            description=description,
        )
        session.add(transaction)

        return True

    async def create_withdrawal_transaction_repository(
            self,
            session: AsyncSession,
            amount: Decimal,
            description: str,
            user_id: int,
            wallet_id: int,
    ) -> bool:

        stmt = select(Wallet).where(
            Wallet.id == wallet_id,
            Wallet.user_id == user_id
        )
        result = await session.execute(stmt)
        wallet = result.scalar_one_or_none()

        if wallet is None:
            raise HTTPException(status_code=404, detail="Кошелек не найден")

        wallet.subtract_balance(amount)

        transaction = self.model(
            wallet_id=wallet_id,
            user_id=user_id,
            transaction_type=TransactionType.WITHDRAWAL.value,
            amount=amount,
            description=description,
        )
        session.add(transaction)

        return True
