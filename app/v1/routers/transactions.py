from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import settings
from app.common.db_depends import get_async_db
from app.common.services.security import decode_access_token
from app.v1.conf.templates import templates
from app.v1.repositories.dependencies import get_transaction_repository, \
    get_wallet_repository
from app.v1.repositories.transactions import TransactionRepository
from app.v1.repositories.wallets import WalletRepository
from app.v1.services.transactions import get_list_transactions_service
from app.v1.services.wallets import get_balance_wallet_user_service, get_wallets_service

router = APIRouter(
    tags=["transactions"]
)


@router.get("/", response_class=HTMLResponse, name="get_list_transactions")
async def get_list_transactions(
        request: Request,
        data: dict = Depends(get_list_transactions_service),
):
    """ Возвращает страницу со списком транзакций """
    return templates.TemplateResponse(
        request=request,
        name="transactions_list.html",
        context={
            "title": "Список транзакций",
            "transactions": data.get("transactions"),
            "users_names": data.get("users_names")

        }
    )


@router.get("/purchases/form", response_class=HTMLResponse, name="create_purchase_form")
async def get_create_purchase_form(
        request: Request,
        balance_user: Decimal = Depends(get_balance_wallet_user_service),
):
    """
    Возвращает страницу с формой создания новой закупки (новая поставка волос)
    """
    return templates.TemplateResponse(
        request=request,
        name="transactions_purchase_create_form.html",
        context={
            "title": "Создание закупки",
            "balance_user": balance_user,
        }
    )


@router.post(
    "/purchases/create",
    response_class=HTMLResponse,
    name="create_purchase_transaction",
)
async def create_purchase_transaction(
        request: Request,
        amount: Decimal = Form(..., description="Сумма закупки"),
        description: str = Form(..., description="Описание закупки"),
        session: AsyncSession = Depends(get_async_db),
        transactions_repo: TransactionRepository = Depends(get_transaction_repository),
        wallets_repo: WalletRepository = Depends(get_wallet_repository),
        balance_wallets: dict = Depends(get_wallets_service)
):
    """
    Создает транзакцию закупки (новая поставка волос)
    """

    token = request.cookies.get(settings.cookie_name)
    payload = decode_access_token(token) if token else None
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user_id = int(payload["user_id"])

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма должна быть больше 0")

    wallet = await wallets_repo.get_wallet_by_user_id(session, user_id)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Кошелек не найден")

    await transactions_repo.create_purchase_transaction_repository(
        session=session,
        amount=amount,
        description=description.strip(),
        user_id=user_id,
        wallet_id=wallet.id,
    )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"balance_wallets": balance_wallets["total_result_all_wallets"]}
    )


@router.get("/transfer/form", response_class=HTMLResponse, name="create_transfer_form")
async def get_transfer_form(
        request: Request,
        balance_user: Decimal = Depends(get_balance_wallet_user_service),
):
    """Возвращает страницу с формой создания новых расходов (коробки, пакеты, зезинки, оплата объявлений)"""

    return templates.TemplateResponse(
        request=request,
        name="transactions_transfer_form.html",
        context={
            "title": "Запись расхода средств",
            "balance_user": balance_user,
        }
    )


@router.post(
    "/transfer/create",
    response_class=HTMLResponse,
    name="create_transfer_transaction",
)
async def create_transfer_transaction(
        request: Request,
        amount: Decimal = Form(..., description="Сумма расхода"),
        description: str = Form(..., description="Описание расхода"),
        session: AsyncSession = Depends(get_async_db),
        transactions_repo: TransactionRepository = Depends(get_transaction_repository),
        wallets_repo: WalletRepository = Depends(get_wallet_repository),
        balance_wallets: dict = Depends(get_wallets_service)

):
    """
    Создает транзакцию расхода средств (пакеты, коробки, зезинки, оплата объявлений
    """
    token = request.cookies.get(settings.cookie_name)
    payload = decode_access_token(token) if token else None
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user_id = int(payload["user_id"])

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма должна быть больше 0")

    try:
        wallet = await wallets_repo.get_wallet_by_user_id(session, user_id)
        if wallet is None:
            raise HTTPException(status_code=404, detail="Кошелек не найден")

        await transactions_repo.create_transfer_transaction_repository(
            session=session,
            amount=amount,
            description=description.strip(),
            user_id=user_id,
            wallet_id=wallet.id,
        )

        await session.commit()
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"balance_wallets": balance_wallets["total_result_all_wallets"]}
        )

    except Exception:
        await session.rollback()
        raise


@router.get("/deposit/form", response_class=HTMLResponse, name="create_deposit_form")
async def get_deposit_form(
        request: Request,
        balance_user: Decimal = Depends(get_balance_wallet_user_service),
):
    """Возвращает страницу с формой создания пополнения (приход) - в случае пополнения кошелька"""

    return templates.TemplateResponse(
        request=request,
        name="transactions_deposit_form.html",
        context={
            "title": "Запись пополнения средств",
            "balance_user": balance_user,
        }
    )


@router.post(
    "/deposit/create",
    response_class=HTMLResponse,
    name="create_deposit_transaction",
)
async def create_deposit_transaction(
        request: Request,
        amount: Decimal = Form(..., description="Сумма пополнения"),
        description: str = Form(..., description="Описание пополнения"),
        session: AsyncSession = Depends(get_async_db),
        transactions_repo: TransactionRepository = Depends(get_transaction_repository),
        wallets_repo: WalletRepository = Depends(get_wallet_repository),
        balance_wallets: dict = Depends(get_wallets_service)
):
    """
    Создает транзакцию пополнения средств (пополнение кошелька)
    """
    token = request.cookies.get(settings.cookie_name)
    payload = decode_access_token(token) if token else None
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user_id = int(payload["user_id"])

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма должна быть больше 0")

    try:
        wallet = await wallets_repo.get_wallet_by_user_id(session, user_id)
        if wallet is None:
            raise HTTPException(status_code=404, detail="Кошелек не найден")

        await transactions_repo.create_deposit_transaction_repository(
            session=session,
            amount=amount,
            description=description.strip(),
            user_id=user_id,
            wallet_id=wallet.id,
        )

        await session.commit()
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"balance_wallets": balance_wallets["total_result_all_wallets"]}

        )

    except Exception:
        await session.rollback()
        raise




@router.get("/withdrawal/form", response_class=HTMLResponse, name="create_withdrawal_form")
async def get_withdrawal_form(
        request: Request,
        balance_user: Decimal = Depends(get_balance_wallet_user_service),
):
    """Возвращает страницу с формой вывода средств (получение зарплаты)"""

    return templates.TemplateResponse(
        request=request,
        name="transactions_withdrawal_form.html",
        context={
            "title": "Запись вывода (получение зарплаты) средств",
            "balance_user": balance_user,
        }
    )



@router.post(
    "/withdrawal/create",
    response_class=HTMLResponse,
    name="create_withdrawal_transaction",
)
async def create_withdrawal_transaction(
        request: Request,
        amount: Decimal = Form(..., description="Сумма вывода"),
        description: str = Form(..., description="Описание вывода средств"),
        session: AsyncSession = Depends(get_async_db),
        transactions_repo: TransactionRepository = Depends(get_transaction_repository),
        wallets_repo: WalletRepository = Depends(get_wallet_repository),
        balance_wallets: dict = Depends(get_wallets_service)

):
    """
    Создает транзакцию вывода средств / Получение зарплаты
    """
    token = request.cookies.get(settings.cookie_name)
    payload = decode_access_token(token) if token else None
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user_id = int(payload["user_id"])

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма должна быть больше 0")

    try:
        wallet = await wallets_repo.get_wallet_by_user_id(session, user_id)
        if wallet is None:
            raise HTTPException(status_code=404, detail="Кошелек не найден")

        await transactions_repo.create_withdrawal_transaction_repository(
            session=session,
            amount=amount,
            description=description.strip(),
            user_id=user_id,
            wallet_id=wallet.id,
        )

        await session.commit()
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"balance_wallets": balance_wallets["total_result_all_wallets"]}
        )

    except Exception:
        await session.rollback()
        raise
