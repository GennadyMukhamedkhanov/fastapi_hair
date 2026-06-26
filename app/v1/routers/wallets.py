from decimal import Decimal
from app.common.services.security import decode_access_token

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import settings
from app.common.db_depends import get_async_db
from app.common.models import Order
from app.common.services.security import get_user_data_from_token
# from app.v1.services.orders import OrderService
from app.v1.conf.templates import templates
from app.v1.enums import OrderStatus
from app.v1.repositories.dependencies import get_order_repository, get_product_repository
from app.v1.repositories.orders import OrderRepository
from app.v1.repositories.products import ProductRepository
from app.v1.schemas.orders import StatusUpdateSchema
from app.v1.services.orders import get_create_order_page_service, \
    create_order_from_form_service, get_orders_page_service, delete_order_service
from app.v1.services.wallets import get_wallets_service, get_wallet_user_service

router = APIRouter(
    tags=["wallets"]
)


@router.get("/", response_class=HTMLResponse, name="wallets_page")
async def get_main_page_wallets(
        request: Request,
        data: dict = Depends(get_wallets_service)
):

    return templates.TemplateResponse(
        request=request,
        name="wallets.html",
        context={
            "total_result_all_wallets": data["total_result_all_wallets"],
            "wallets_list_users": data["wallets_list_users"],

        },
    )


@router.get("/{user_id}", response_class=HTMLResponse, name="wallet_user_page")
async def get_wallet_user(
        user_id: int,
        request: Request,
        data: dict = Depends(get_wallet_user_service)
):
    token = request.cookies.get(settings.cookie_name)
    payload = decode_access_token(token) if token else None

    if payload is None:
        raise HTTPException(status_code=401, detail="Не авторизован")

    token_user_id = payload.get("user_id", "") if payload else ""
    name = payload.get("name", "") if payload else ""

    if token_user_id != user_id:
        return RedirectResponse(url="/v1/wallets", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="wallet_detail.html",
        context={
            "wallet_user": data.get("wallet_user"),
            "name": name
        }
    )
