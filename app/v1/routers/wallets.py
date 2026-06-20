from decimal import Decimal

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
from app.v1.services.wallets import get_wallets_service

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
