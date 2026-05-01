from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.common.config import settings
from fastapi import HTTPException


def create_access_token(email: str, name: str, user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": email,
        "name": name,
        "user_id": user_id,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.jwt_expire_days)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.PyJWTError:
        return None


def get_user_data_from_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("user_id")
        user_email = payload.get("sub")
        user_name = payload.get("name")
        return {
            'user_id': user_id,
            'email': user_email,
            'name': user_name
        }

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Неверный токен")
