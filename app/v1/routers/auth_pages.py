from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from app.common.config import settings
from app.common.services.cookies import set_auth_cookie, clear_auth_cookie
from app.common.services.email_service import send_verification_code

from app.common.services.security import create_access_token, decode_access_token
from app.common.services.auth_memory import auth_memory_store
from app.v1.conf.templates import templates
from app.v1.repositories.dependencies import get_user_repository
from app.v1.repositories.users import UserRepository
from app.v1.services.user import create_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.db_depends import get_async_db

router = APIRouter(
    tags=["auth_pages"]
)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """ Cтраница ввода email"""
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "app_name": settings.app_name,
            "error": None,
            "email": "",
        },
    )


@router.post("/login/send-code", response_class=HTMLResponse)
async def send_code_for_login(request: Request, email: str = Form(...)):
    ''' Отправляет код на email'''
    email = email.strip().lower()

    if email not in settings.allowed_emails:
        return templates.TemplateResponse(
            request=request,
            name="forbidden.html",
            context={
                "request": request,
                "app_name": settings.app_name,
                "email": email,
            },
            status_code=403,
        )

    code = auth_memory_store.generate_code(email)
    await send_verification_code(email, code)

    return templates.TemplateResponse(
        request=request,
        name="verify.html",
        context={
            "request": request,
            "app_name": settings.app_name,
            "email": email,
            "error": None,
            "mode": "login",
        },
    )


@router.post("/verify", response_class=HTMLResponse)
async def verify_login_code(
        request: Request,
        email: str = Form(...),
        name: str = Form(...),
        code: str = Form(...),
        session: AsyncSession = Depends(get_async_db),
        users_repo: UserRepository = Depends(get_user_repository)
):
    '''Подтверждение кода после входа'''
    email = email.strip().lower()
    code = code.strip()

    ok, message = auth_memory_store.verify_code(email, code)
    if not ok:
        return templates.TemplateResponse(
            request=request,
            name="verify.html",
            context={
                "request": request,
                "app_name": settings.app_name,
                "email": email,
                "error": message,
                "mode": "login",
            },
            status_code=400,
        )

    user_id = await create_user(email, name, session, users_repo)

    token = create_access_token(email, name, user_id)
    response = RedirectResponse(url="/v1/index/", status_code=303)
    set_auth_cookie(response, token)

    return response


@router.get("/renew", response_class=HTMLResponse)
async def renew_page(request: Request):
    token = request.cookies.get(settings.cookie_name)
    payload = decode_access_token(token) if token else None
    email = payload.get("sub", "") if payload else ""

    return templates.TemplateResponse(
        request=request,
        name="renew.html",
        context={
            "request": request,
            "app_name": settings.app_name,
            "email": email,
            "error": None,
            "code_sent": False,
        },
    )


@router.post("/renew/send-code", response_class=HTMLResponse)
async def send_code_for_renew(request: Request, email: str = Form(...)):
    '''Отправить код для продления'''
    email = email.strip().lower()

    if email not in settings.allowed_emails:
        return templates.TemplateResponse(
            request=request,
            name="forbidden.html",
            context={
                "request": request,
                "app_name": settings.app_name,
                "email": email,
            },
            status_code=403,
        )

    code = auth_memory_store.generate_code(email)
    await send_verification_code(email, code)

    return templates.TemplateResponse(
        request=request,
        name="renew.html",
        context={
            "request": request,
            "app_name": settings.app_name,
            "email": email,
            "error": None,
            "code_sent": True,
        },
    )


@router.post("/renew/confirm", response_class=HTMLResponse)
async def renew_confirm(
        request: Request,
        email: str = Form(...),
        code: str = Form(...),
):
    '''Подтвердить код для продления'''
    email = email.strip().lower()
    code = code.strip()

    ok, message = auth_memory_store.verify_code(email, code)
    if not ok:
        return templates.TemplateResponse(
            request=request,
            name="renew.html",
            context={
                "request": request,
                "app_name": settings.app_name,
                "email": email,
                "error": message,
                "code_sent": True,
            },
            status_code=400,
        )

    token = create_access_token(email)
    response = RedirectResponse(url="/v1/index/", status_code=303)
    set_auth_cookie(response, token)
    return response


@router.get("/logout")
async def logout():
    '''Очистить cookie и выйти'''
    response = RedirectResponse(url="/v1/auth_pages/login", status_code=303)
    clear_auth_cookie(response)
    return response


@router.get("/forbidden", response_class=HTMLResponse)
async def forbidden_page(request: Request):
    '''Страница отказа в доступе'''
    return templates.TemplateResponse(
        request=request,
        name="forbidden.html",
        context={
            "request": request,
            "app_name": settings.app_name,
            "email": None,
        },
        status_code=403,
    )
