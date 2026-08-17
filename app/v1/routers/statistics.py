from fastapi import APIRouter, HTTPException
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.common.config import settings
from app.common.services.security import decode_access_token
# from app.v1.services.orders import OrderService
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
