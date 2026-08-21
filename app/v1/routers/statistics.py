from fastapi import APIRouter, HTTPException, status, Depends
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.common.config import settings
from app.common.db_depends import get_async_db
from app.common.services.security import decode_access_token
# from app.v1.services.orders import OrderService
from app.v1.conf.templates import templates
from app.v1.repositories.dependencies import get_sales_repository
from app.v1.repositories.statistics import SalesRepository
from app.v1.services.statistics import get_all_sales_services
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.v1.conf.templates import templates


# Создаём маршрутизатор с префиксом и тегом
router = APIRouter(
    tags=["statistics"]
)


@router.get("/", response_class=HTMLResponse)
async def get_page_statistics(
        request: Request
):
    token = request.cookies.get(settings.cookie_name)
    payload = decode_access_token(token) if token else None

    if payload is None:
        raise HTTPException(status_code=401, detail="Не авторизован")

    token_user_mail = payload.get("sub", None) if payload else None
    ddd = settings.mail_user_from_backups
    if token_user_mail != settings.mail_user_from_backups:
        button_backups = False
    else:
        button_backups = True

    return templates.TemplateResponse(
        request=request,
        name="statistics.html",
        context={
            "title": "Статистика, аналитика и отчёты",
            "button_backups": button_backups

        }
    )


# ============================================
# СТРАНИЦА СТАТИСТИКИ ПРОДАЖ
# ============================================

@router.get("/sales", response_class=HTMLResponse)
async def get_sales_statistics_page(
        request: Request,
        year: Optional[int] = Query(None, description="Год для фильтрации"),
        months: int = Query(6, description="Количество месяцев для recent"),
        session: AsyncSession = Depends(get_async_db),
        sales_repo: SalesRepository = Depends(get_sales_repository),
):
    """
    Страница статистики продаж.

    Параметры:
    - year — год для фильтрации (по умолчанию текущий)
    - months — количество месяцев для блока "последние продажи"
    """

    # Получаем все данные через сервис
    data = await get_all_sales_services(
        session=session,
        sales_repo=sales_repo,
        year=year,
        months=months
    )

    # Определяем, есть ли данные
    has_data = data["stats"]["sales_count"] > 0

    return templates.TemplateResponse(
        request=request,
        name="sales_statistics.html",
        context={
            "title": "Статистика продаж",
            "stats": data["stats"],
            "monthly": data["monthly"],
            "recent": data["recent"],
            "all_years": data["all_years"],
            "yearly_summary": data["yearly_summary"],
            "chart_data": data["chart_data"],
            "available_years": data["available_years"],
            "current_year": data["current_year"],
            "months_count": data["months_count"],
            "has_data": has_data,
            "request": request,
        }
    )