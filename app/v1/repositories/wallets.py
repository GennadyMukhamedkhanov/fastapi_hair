from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import select, func, case, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.models import Order, OrderItem, Wallet, User
from app.common.models.hairs import HairProduct, HairTone
from app.v1.enums import ProductStatusEnum, OrderStatus
from app.v1.repositories.common import CommonRepository
from app.v1.schemas.orders import OrderCreateSchema


class WalletRepository(CommonRepository):
    model = Wallet

    async def get_all_wallets_users(
            self,
            session: AsyncSession

    ) -> list[Wallet]:
        stmt = select(self.model).options(selectinload(self.model.user))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_wallet_by_user_id(
            self,
            session: AsyncSession,
            user_id: int,

    ) -> Wallet:
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        result = await session.execute(stmt)
        wallet = result.scalar_one_or_none()
        return wallet

