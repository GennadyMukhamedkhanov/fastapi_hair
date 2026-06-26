from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import settings
from app.common.db_depends import get_async_db
from app.common.models import HairProduct
from app.common.services.security import decode_access_token
from app.v1.repositories.dependencies import get_product_repository, get_wallet_repository
from app.v1.repositories.products import ProductRepository
from app.v1.repositories.wallets import WalletRepository
from app.v1.schemas.products import ProductUpdateSchema
from app.v1.utils.hair import tone_and_length_sort_key
from fastapi import APIRouter, Depends, status, HTTPException


async def get_wallets_service(
        session: AsyncSession = Depends(get_async_db),
        wallets_repo: WalletRepository = Depends(get_wallet_repository)
):
    wallets_list_users = await wallets_repo.get_all_wallets_users(session)
    total_result_all_wallets = sum(wallet.balance for wallet in wallets_list_users)

    return {
        "wallets_list_users": wallets_list_users,
        "total_result_all_wallets": total_result_all_wallets

    }


async def get_wallet_user_service(
        request: Request,
        user_id: int,
        session: AsyncSession = Depends(get_async_db),
        wallets_repo: WalletRepository = Depends(get_wallet_repository)

):

    wallet_user = await wallets_repo.get_wallet_by_user_id(session, user_id)

    return {
        "wallet_user": wallet_user
    }



async def get_balance_wallet_user_service(
        request: Request,
        session: AsyncSession = Depends(get_async_db),
        wallets_repo: WalletRepository = Depends(get_wallet_repository)

):
    token = request.cookies.get(settings.cookie_name)
    payload = decode_access_token(token) if token else None

    if payload is None:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user_id = payload.get("user_id", "") if payload else ""

    wallet_user = await wallets_repo.get_wallet_by_user_id(session, user_id)

    return  wallet_user.balance
