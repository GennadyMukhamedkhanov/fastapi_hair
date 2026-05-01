from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.v1.conf.templates import templates
from app.common.config import settings

router = APIRouter(
    tags=["site_pages"]
)


@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request": request,
            "app_name": settings.app_name,
            "user_email": request.state.user_email,
        },
    )
