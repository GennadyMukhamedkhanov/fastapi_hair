from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.common.database import Base
import sys
import os
from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url

# Загружаем .env файл
env_path = os.path.join(os.path.dirname(__file__), '../../..', 'app', '.env')
load_dotenv(dotenv_path=env_path)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.common.models import *

config = context.config

# ✅ Безопасно получаем URL из переменной окружения
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Преобразуем asyncpg URL в обычный для миграций
    if "+asyncpg" in database_url:
        database_url = database_url.replace("+asyncpg", "")

    # Устанавливаем URL в конфиг Alembic
    config.set_main_option("sqlalchemy.url", database_url)

    # Для отладки (скрываем пароль)
    url_obj = make_url(database_url)
    print(f"✅ Database: {url_obj.drivername}://{url_obj.username}:***@{url_obj.host}:{url_obj.port}/{url_obj.database}")
else:
    raise ValueError("DATABASE_URL environment variable not set")

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()