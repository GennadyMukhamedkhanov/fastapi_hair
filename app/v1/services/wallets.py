from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db_depends import get_async_db
from app.common.models import HairProduct
from app.v1.repositories.dependencies import get_product_repository, get_wallet_repository
from app.v1.repositories.products import ProductRepository
from app.v1.repositories.wallets import WalletRepository
from app.v1.schemas.products import ProductUpdateSchema
from app.v1.utils.hair import tone_and_length_sort_key


async def get_wallets_service(
        session: AsyncSession = Depends(get_async_db),
        products_repo: WalletRepository = Depends(get_wallet_repository)
):
    wallets_list_users = await products_repo.get_all_wallets_users(session)
    total_result_all_wallets = sum(wallet.balance for wallet in wallets_list_users)

    return {
        "wallets_list_users": wallets_list_users,
        "total_result_all_wallets": total_result_all_wallets

    }
