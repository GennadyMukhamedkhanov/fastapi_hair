# --------------- Асинхронное подключение к PostgreSQL -------------------------

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Строка подключения
DATABASE_URL = "postgresql+asyncpg://hair_user:198616Gm@localhost:5432/hair_db"


# ОБЯЗАТЕЛЬНО СНАЧАЛА БАЗА
class Base(DeclarativeBase):
    pass


# ТЕПЕРЬ ИМПОРТИРУЕМ МОДЕЛИ ПОСЛЕ Base
from app.common.models.orders import Order, OrderItem
from app.common.models.hairs import HairTone, HairProduct

# Теперь создаём engine после Base и моделей
async_engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)

__all__ = [
    "Base",
    "async_engine",
    "async_session_maker",
    "User",
    "Order",
    "HairTone",
    "HairProduct",
    "OrderItem",
]
