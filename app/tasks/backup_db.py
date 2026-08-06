# app/tasks/backup_db.py
from app.celery_app import celery_app
import logging
import os
import subprocess
import datetime
from pathlib import Path
from typing import Dict, Any
import shutil
import gzip

logger = logging.getLogger(__name__)


def get_backup_dir() -> Path:
    """
    Определяет директорию для бэкапов с автоматическим созданием
    """
    # Приоритет 1: Используем переменную окружения
    env_dir = os.getenv('BACKUP_DIR')
    if env_dir:
        backup_dir = Path(env_dir)
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            # Проверяем права на запись
            test_file = backup_dir / '.write_test'
            test_file.touch()
            test_file.unlink()
            logger.info(f"✅ Используем директорию из ENV: {backup_dir}")
            return backup_dir
        except Exception as e:
            logger.warning(f"⚠️ Не удалось использовать BACKUP_DIR={env_dir}: {e}")

    # Приоритет 2: Монтированная папка в Docker
    docker_backup = Path("/app/backups")
    if docker_backup.exists() and os.access(docker_backup, os.W_OK):
        logger.info(f"✅ Используем Docker volume: {docker_backup}")
        return docker_backup

    # Приоритет 3: Создаем в /app/backups (с проверкой прав)
    try:
        docker_backup.mkdir(parents=True, exist_ok=True)
        # Проверяем права
        test_file = docker_backup / '.write_test'
        test_file.touch()
        test_file.unlink()
        logger.info(f"✅ Используем /app/backups: {docker_backup}")
        return docker_backup
    except Exception as e:
        logger.warning(f"⚠️ Не удалось использовать /app/backups: {e}")

    # Приоритет 4: Используем /tmp (всегда есть права)
    tmp_backup = Path("/tmp/backups")
    tmp_backup.mkdir(parents=True, exist_ok=True)
    logger.info(f"✅ Используем временную директорию: {tmp_backup}")
    return tmp_backup


# Глобальная директория для бэкапов
BACKUP_DIR = get_backup_dir()


@celery_app.task(name='app.tasks.backup_db.create_backup_db')
def create_backup_db() -> Dict[str, Any]:
    """
    Создает сжатую резервную копию базы данных PostgreSQL
    """
    try:
        # Проверяем доступность pg_dump
        pg_dump_path = shutil.which('pg_dump')
        if not pg_dump_path:
            return {
                "status": "error",
                "executed_at": str(datetime.datetime.now()),
                "error": "pg_dump не найден. Установите postgresql-client"
            }

        # Формируем имя файла
        now = datetime.datetime.now()
        date_string = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"backup_db_{date_string}.sql"
        filepath = BACKUP_DIR / filename
        compressed_file = BACKUP_DIR / f"{filename}.gz"

        logger.info(f"⏰ Создание бэкапа: {filepath}")

        # Параметры БД
        db_name = os.getenv('POSTGRES_DB', 'fastapi_hair')
        db_user = os.getenv('POSTGRES_USER', 'postgres')
        db_host = os.getenv('POSTGRES_HOST', 'db')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_password = os.getenv('POSTGRES_PASSWORD', '')

        # Команда pg_dump
        cmd = [
            pg_dump_path,
            "-U", db_user,
            "-h", db_host,
            "-p", db_port,
            "-d", db_name,
            "-F", "p",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
        ]

        env = os.environ.copy()
        if db_password:
            env["PGPASSWORD"] = db_password

        # Выполняем pg_dump
        with open(filepath, "w", encoding="utf-8") as f:
            subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                check=True,
                env=env,
                text=True,
                timeout=300
            )

        # Сжимаем бэкап
        logger.info(f"📦 Сжатие бэкапа...")
        with open(filepath, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb', compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Получаем размеры для сравнения
        original_size = filepath.stat().st_size
        compressed_size = compressed_file.stat().st_size
        compression_ratio = (1 - compressed_size / original_size) * 100

        # Удаляем несжатый файл
        filepath.unlink()

        logger.info(f"✅ Бэкап создан и сжат: {compressed_file}")
        logger.info(f"   Оригинал: {original_size / 1024:.2f} KB")
        logger.info(f"   Сжатый: {compressed_size / 1024:.2f} KB")
        logger.info(f"   Экономия: {compression_ratio:.1f}%")

        # Проверяем свободное место
        free_space = shutil.disk_usage(BACKUP_DIR).free
        free_gb = free_space / (1024 ** 3)

        # Очищаем старые бэкапы (ищем .sql и .sql.gz)
        cleanup_old_backups(keep_last=30)

        return {
            "status": "success",
            "executed_at": str(now),
            "backup_file": str(compressed_file),
            "original_size_kb": round(original_size / 1024, 2),
            "compressed_size_kb": round(compressed_size / 1024, 2),
            "compressed_size_mb": round(compressed_size / (1024 * 1024), 2),
            "compression_ratio": round(compression_ratio, 1),
            "free_space_gb": round(free_gb, 2),
            "kept_backups": 30,
            "message": f"Сжатый бэкап создан успешно (экономия {compression_ratio:.1f}%)"
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "executed_at": str(datetime.datetime.now()),
            "error": "Превышено время выполнения (5 минут)"
        }
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else "Нет сообщения"
        logger.error(f"❌ Ошибка pg_dump: {error_msg}")
        return {
            "status": "error",
            "executed_at": str(datetime.datetime.now()),
            "error": f"Ошибка pg_dump: {error_msg}"
        }
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        return {
            "status": "error",
            "executed_at": str(datetime.datetime.now()),
            "error": str(e)
        }


def cleanup_old_backups(keep_last: int = 30):
    """Удаляет старые бэкапы (.sql и .sql.gz)"""
    try:
        # Ищем все файлы бэкапов (.sql и .sql.gz)
        backup_files = []
        backup_files.extend(BACKUP_DIR.glob("backup_db_*.sql"))
        backup_files.extend(BACKUP_DIR.glob("backup_db_*.sql.gz"))

        # Сортируем по времени модификации (новые сверху)
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        total = len(backup_files)
        logger.info(f"📊 Найдено бэкапов: {total}, нужно оставить: {keep_last}")

        if total > keep_last:
            deleted = 0
            for old_file in backup_files[keep_last:]:
                try:
                    old_file.unlink()
                    logger.info(f"🗑️ Удален старый бэкап: {old_file}")
                    deleted += 1
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось удалить {old_file}: {e}")
            logger.info(f"🧹 Удалено {deleted} старых бэкапов. Осталось {keep_last} файлов")
        else:
            logger.info(f"🧹 Старых бэкапов для удаления нет (всего {total} файлов)")

    except Exception as e:
        logger.warning(f"⚠️ Ошибка очистки: {e}")


@celery_app.task(name='app.tasks.backup_db.cleanup_backups_manual')
def cleanup_backups_manual(keep_last: int = 30) -> Dict[str, Any]:
    """
    Задача для ручной очистки старых бэкапов
    """
    try:
        # Ищем все файлы бэкапов (.sql и .sql.gz)
        backup_files = []
        backup_files.extend(BACKUP_DIR.glob("backup_db_*.sql"))
        backup_files.extend(BACKUP_DIR.glob("backup_db_*.sql.gz"))

        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        total = len(backup_files)
        deleted = 0

        if total > keep_last:
            for old_file in backup_files[keep_last:]:
                try:
                    old_file.unlink()
                    deleted += 1
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось удалить {old_file}: {e}")

        # Проверяем свободное место
        free_space = shutil.disk_usage(BACKUP_DIR).free
        free_gb = free_space / (1024 ** 3)

        return {
            "status": "success",
            "total_files": total,
            "deleted_count": deleted,
            "kept_last": keep_last,
            "remaining_files": total - deleted,
            "free_space_gb": round(free_gb, 2),
            "message": f"Удалено {deleted} старых бэкапов. Осталось {total - deleted} файлов. Свободно: {free_gb:.2f} GB"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }