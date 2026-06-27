# app/common/config.py
from __future__ import annotations
from typing import Set
import os
from dotenv import load_dotenv
from pathlib import Path
from dataclasses import dataclass, field

# ✅ Явно указываем путь к .env
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env.prod"  # Раскомментировать для продакшена
#env_path = BASE_DIR / ".env"  # Использовать для разработки

if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Загружен .env из: {env_path}")
else:
    # fallback — ищем в текущей директории
    load_dotenv()
    print(f"⚠️ .env не найден по пути {env_path}, ищем в текущей: {os.getcwd()}")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


def _split_emails(raw: str) -> Set[str]:
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "Private Site")
    app_env: str = os.getenv("APP_ENV", "dev")

    jwt_secret: str = os.getenv("JWT_SECRET", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_days: int = int(os.getenv("JWT_EXPIRE_DAYS", "30"))

    cookie_name: str = os.getenv("COOKIE_NAME", "access_token")
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "lax")

    allowed_emails: Set[str] = field(default_factory=lambda: _split_emails(os.getenv("ALLOWED_EMAILS", "")))

    mail_smtp_host: str = os.getenv("MAIL_SMTP_HOST", "smtp.mail.ru")
    mail_smtp_port: int = int(os.getenv("MAIL_SMTP_PORT", "587"))
    mail_smtp_user: str = os.getenv("MAIL_SMTP_USER", "")
    mail_smtp_password: str = os.getenv("MAIL_SMTP_PASSWORD", "")
    mail_from: str = os.getenv("MAIL_FROM", "")

    verify_code_ttl_minutes: int = int(os.getenv("VERIFY_CODE_TTL_MINUTES", "10"))
    verify_max_attempts: int = int(os.getenv("VERIFY_MAX_ATTEMPTS", "5"))

    # Redis настройки
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: str | None = os.getenv("REDIS_PASSWORD", None)

    class Config:
        env_file = ".env.prod"
        extra = "ignore"  # Игнорировать лишние переменные


settings = Settings()

# Отладка
print(f"✅ Загружено {len(settings.allowed_emails)} email: {settings.allowed_emails}")