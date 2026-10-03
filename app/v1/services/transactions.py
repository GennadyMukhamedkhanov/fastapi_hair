from fastapi import Depends, Request, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.common.config import settings
from app.common.db_depends import get_async_db
from app.common.models import HairProduct
from app.common.services.security import decode_access_token
from app.v1.repositories.dependencies import get_product_repository, get_wallet_repository, get_transaction_repository, \
    get_user_repository
from app.v1.repositories.products import ProductRepository
from app.v1.repositories.transactions import TransactionRepository
from app.v1.repositories.users import UserRepository
from app.v1.repositories.wallets import WalletRepository
from app.v1.schemas.products import ProductUpdateSchema
from app.v1.utils.hair import tone_and_length_sort_key
from datetime import timezone, timedelta


MSK = timezone(timedelta(hours=3))

def format_moscow_datetime(dt):
    """Форматирует datetime в московское время (dd.mm.YYYY HH:MM)"""
    if dt is None:
        return None
    # Если datetime без таймзоны, добавляем UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Конвертируем в московское время
    msk_dt = dt.astimezone(MSK)
    return msk_dt.strftime('%d.%m.%Y %H:%M')

async def get_list_transactions_service(
        session: AsyncSession = Depends(get_async_db),
        transactions_repo: TransactionRepository = Depends(get_transaction_repository),
        users_repo: UserRepository = Depends(get_user_repository),
):
    transactions = await transactions_repo.get_all_transactions(session)
    transactions_list = [
        {
            "id": transaction.id,
            "wallet_id": transaction.wallet_id,
            "username": transaction.user.username if transaction.user else None,
            "user_email": transaction.user.email if transaction.user else None,
            "transaction_type": transaction.transaction_type,
            "sale_amount": str(transaction.sale_amount) if transaction.sale_amount is not None else None,
            "cost_amount": str(transaction.cost_amount) if transaction.cost_amount is not None else None,
            "profit_amount": str(transaction.profit_amount) if transaction.profit_amount is not None else None,
            "amount": str(transaction.amount) if transaction.amount is not None else None,
            "description": transaction.description if transaction.description else None,
            "created_at": transaction.created_at.isoformat() if transaction.created_at else None,
            "created_at_display": format_moscow_datetime(transaction.created_at)
        }
        for transaction in transactions
    ]

    sorted_transactions = sorted(transactions_list, key=lambda x: x['id'], reverse=True)

    users_list = await users_repo.get_list_name_users(session)
    users_names = [user.username for user in users_list]

    return {
        "transactions": sorted_transactions,
        "users_names": users_names
    }
