from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import select, desc, func, case, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.models import Order, OrderItem, Wallet, WalletTransaction
from app.common.models.hairs import HairProduct, HairTone
from app.v1.enums import ProductStatusEnum, OrderStatus
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
