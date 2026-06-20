# --------------- Асинхронное подключение к PostgreSQL -------------------------
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

# Получаем DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL не установлен в переменных окружения")

# Убеждаемся, что используется asyncpg драйвер
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Для production берем из переменной окружения
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Создаем движок с разными настройками для dev и prod
if DEBUG:
    # Настройки для разработки (более простые)
    async_engine = create_async_engine(
        DATABASE_URL,
        echo=True,          # Логируем все SQL запросы
        future=True,
        pool_size=5,        # Маленький пул для разработки
        max_overflow=2,     # Небольшой запас
    )
else:
    # Настройки для production (оптимизированные)
    async_engine = create_async_engine(
        DATABASE_URL,
        echo=False,         # Не логируем SQL в prod
        future=True,
        pool_size=20,       # Большой пул соединений
        max_overflow=10,    # Запасные соединения
        pool_pre_ping=True, # Проверяем соединения перед использованием
        pool_recycle=3600,  # Пересоздаем соединения через час
    )

# Создаем фабрику сессий
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей
class Base(DeclarativeBase):
    pass


# Экспортируем все необходимые объекты
__all__ = [
    "Base",
    "async_engine",
    "async_session_maker",

]