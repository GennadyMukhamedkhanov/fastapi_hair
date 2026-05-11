from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.config import settings
from app.common.services.security import decode_access_token


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Публичные пути (не требуют авторизации)
        public_paths = {
            "/v1/auth_pages/login",
            "/v1/auth_pages/login/send-code",
            "/v1/auth_pages/verify",
            "/v1/auth_pages/renew",
            "/v1/auth_pages/renew/send-code",
            "/v1/auth_pages/renew/confirm",
            "/v1/auth_pages/logout",
            "/v1/auth_pages/forbidden",
            "/v1/index",
            "/v1/index/",
            "/",
            "/health",
            "/redis-status",
        }

        path = request.url.path

        # Разрешаем доступ к статическим файлам и публичным путям
        if path.startswith("/v1/static") or path in public_paths:
            return await call_next(request)

        # Проверяем токен
        token = request.cookies.get(settings.cookie_name)
        if not token:
            return RedirectResponse(url="/v1/auth_pages/login", status_code=303)

        # Декодируем токен
        payload = decode_access_token(token)
        if not payload:
            response = RedirectResponse(url="/v1/auth_pages/login", status_code=303)
            response.delete_cookie(settings.cookie_name)
            return response

        # Проверяем email в разрешенных
        email = str(payload.get("sub", "")).lower()
        if email not in settings.allowed_emails:
            return RedirectResponse(url="/v1/auth_pages/forbidden", status_code=303)

        request.state.user_email = email
        return await call_next(request)