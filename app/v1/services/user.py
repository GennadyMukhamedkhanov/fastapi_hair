from sqlalchemy.ext.asyncio import AsyncSession

from app.v1.repositories.users import UserRepository


async def create_user(
        email: str,
        name: str,
        session: AsyncSession,
        users_repo: UserRepository,

) -> int:
    user_id = await users_repo.create_user(session, email, name)

    return user_id
