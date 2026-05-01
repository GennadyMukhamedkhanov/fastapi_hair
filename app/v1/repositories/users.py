from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4
from app.v1.auth import hash_password
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.models import Order, OrderItem, User
from app.common.models.hairs import HairProduct
from app.v1.enums import ProductStatusEnum, OrderStatus
from app.v1.repositories.common import CommonRepository
from app.v1.schemas.orders import OrderCreateSchema


class UserRepository(CommonRepository):
    model = User

    async def create_user(
            self,
            session: AsyncSession,
            email: str,
            name: str
    ) -> int:
        """Создаёт пользователя, если его ещё нет"""
        # Проверяем существование
        stmt = select(self.model).where(self.model.email == email)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing.id

        # Создаём нового
        password = 'password'  # TODO: изменить, password = 'password' временно
        user = self.model(email=email,
                          username=name,
                          hashed_password=hash_password(password))
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user.id
