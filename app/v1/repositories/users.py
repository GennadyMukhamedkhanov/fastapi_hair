from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from app.common.models import User, Wallet
from app.v1.auth import hash_password
from app.v1.repositories.common import CommonRepository


class UserRepository(CommonRepository):
    model = User

    async def create_user(
            self,
            session: AsyncSession,
            email: str,
            name: str
    ) -> int:
        """Создаёт пользователя с кошельком через связь"""
        # Проверяем существование
        stmt = select(self.model).where(self.model.email == email)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing.id

        try:
            password = 'password'  # TODO: изменить
            user = self.model(
                email=email,
                username=name,
                hashed_password=hash_password(password)
            )

            #  Создаем кошелек
            wallet = Wallet(balance=Decimal("0.00"))
            user.wallet = wallet  # SQLAlchemy сам подставит user_id

            session.add(user)

            await session.commit()
            await session.refresh(user)

            return user.id

        except Exception as e:
            await session.rollback()
            raise ValueError(f"Ошибка создания пользователя: {str(e)}")
