import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker

logger = logging.getLogger(__name__)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Предоставляет асинхронную сессию SQLAlchemy для работы с базой данных.
    Автоматически управляет транзакциями и закрытием сессии.
    """

    async with async_session_maker() as session:
        try:
            logger.debug("Database session created")
            yield session
            await session.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            logger.error(f"Error during database operation: {e}")
            await session.rollback()
            logger.debug("Transaction rolled back")
            raise  # ❗ ВАЖНО: пробрасываем исключение дальше
        finally:
            await session.close()
            logger.debug("Database session closed")

