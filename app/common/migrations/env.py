from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.common.database import Base  # ваши модели
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata  # метаданные моделей


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
        # ПЕЧАТАЕМ ВСЕ ТАБЛИЦЫ ИЗ БАЗЫ И ИЗ METADATA
        print("\n=== ALEMBIC SEES TABLES FROM DATABASE ===")
        db_tables = connection.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        for row in db_tables.fetchall():
            print(f"DB TABLE: {row[0]}")

        print("\n=== ALEMBIC SEES TABLES FROM Base.metadata ===")
        for table in Base.metadata.sorted_tables:
            print(f"METADATA TABLE: {table.name}")

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
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
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
