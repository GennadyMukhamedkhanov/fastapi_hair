from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from app.v1.conf.templates import templates
from app.v1.services.wallets import get_wallets_service

# Создаём маршрутизатор с префиксом и тегом
router = APIRouter(
    tags=["index"]
)


@router.get("/", response_class=HTMLResponse)
async def home(
        request: Request,
        balance_wallets: dict = Depends(get_wallets_service)):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Создание закупки",
            "balance_wallets": balance_wallets["total_result_all_wallets"]
        }
    )
