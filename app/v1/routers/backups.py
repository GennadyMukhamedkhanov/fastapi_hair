import os
import gzip
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.common.config import settings
from app.common.services.security import decode_access_token
from app.v1.conf.templates import templates

# Импортируем задачи Celery для создания бэкапа
from app.tasks.backup_db import create_backup_db, get_backup_dir

router = APIRouter(
    tags=["backups"]
)

# Используем ту же директорию, что и в Celery
BACKUP_DIR = get_backup_dir()


@router.get("/", response_class=HTMLResponse)
async def get_page_forms_backup(request: Request):
    """Страница управления бэкапами"""
    token = request.cookies.get(settings.cookie_name)
    payload = decode_access_token(token) if token else None

    if payload is None:
        raise HTTPException(status_code=401, detail="Не авторизован")

    token_user_mail = payload.get("sub", None) if payload else None

    if token_user_mail is None or token_user_mail != settings.mail_user_from_backups:
        return RedirectResponse(url="/v1/statistics", status_code=303)

    # Получаем список бэкапов
    backups = get_backups_list()

    return templates.TemplateResponse(
        request=request,
        name="backups.html",
        context={
            "title": "Управление резервными копиями",
            "backups": backups,
            "backup_count": len(backups)
        }
    )


def get_backups_list() -> List[Dict[str, Any]]:
    """
    Получает список файлов бэкапов (.sql.gz) с их размером и датой
    """
    backups = []

    if not BACKUP_DIR.exists():
        return backups

    # Ищем только сжатые файлы .gz
    for file in sorted(BACKUP_DIR.glob("backup_db_*.sql.gz"), reverse=True):
        stat = file.stat()
        size_mb = stat.st_size / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB"

        # Извлекаем дату из имени файла
        # Формат: backup_db_2026-08-11_14-30-00.sql.gz
        name_parts = file.stem.replace("backup_db_", "").split("_")
        if len(name_parts) >= 2:
            date_str = name_parts[0] + " " + name_parts[1].replace("-", ":")
        else:
            date_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        backups.append({
            "name": file.name,
            "path": str(file),
            "size": size_str,
            "size_bytes": stat.st_size,
            "created_at": date_str,
            "created_timestamp": stat.st_mtime
        })

    return backups


@router.post("/create")
async def create_backup():
    """
    Запускает создание бэкапа через Celery
    """
    try:
        # Запускаем задачу Celery асинхронно
        task = create_backup_db.delay()

        return {
            "status": "success",
            "message": "Задача на создание бэкапа запущена",
            "task_id": task.id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска задачи: {str(e)}")


@router.get("/status/{task_id}")
async def get_backup_status(task_id: str):
    """
    Проверяет статус выполнения задачи
    """
    from app.celery_app import celery_app

    task = celery_app.AsyncResult(task_id)

    if task.status == 'PENDING':
        return {"status": "pending", "message": "Задача ожидает выполнения"}
    elif task.status == 'STARTED':
        return {"status": "started", "message": "Задача выполняется"}
    elif task.status == 'SUCCESS':
        result = task.result
        return {
            "status": "success",
            "message": "Бэкап создан",
            "result": result
        }
    elif task.status == 'FAILURE':
        return {
            "status": "error",
            "message": str(task.info)
        }
    else:
        return {"status": "unknown", "message": task.status}


@router.post("/restore")
async def restore_backup(request: Request):
    try:
        data = await request.json()
        filename = data.get("filename")

        if not filename:
            raise HTTPException(status_code=400, detail="Не указан файл бэкапа")

        filepath = BACKUP_DIR / filename

        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Файл бэкапа не найден")

        if not filename.endswith('.gz'):
            raise HTTPException(status_code=400, detail="Файл должен быть сжатым (.gz)")

        temp_file = BACKUP_DIR / f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

        try:
            # 👇 РАСПАКОВЫВАЕМ И ФИЛЬТРУЕМ
            with gzip.open(filepath, 'rb') as f_in:
                content = f_in.read().decode('utf-8')

            # Удаляем проблемные строки с transaction_timeout
            lines = content.splitlines()
            filtered_lines = [
                line for line in lines
                if 'transaction_timeout' not in line.lower()
            ]
            filtered_content = '\n'.join(filtered_lines)

            # Сохраняем во временный файл
            temp_file.write_text(filtered_content, encoding='utf-8')

            db_name = settings.db_name
            db_user = settings.db_user
            db_host = settings.db_host
            db_port = settings.db_port
            db_password = settings.db_password

            print(f"🔍 Восстановление: {filename}")
            print(f"📊 БД: {db_name}, Пользователь: {db_user}, Хост: {db_host}")
            print(f"🔑 Пароль: {'***' if db_password else '⚠️ ПАРОЛЬ ПУСТОЙ!'}")

            cmd = [
                "psql",
                "-U", db_user,
                "-h", db_host,
                "-p", db_port,
                "-d", db_name,
                "-v", "ON_ERROR_STOP=1",
                "--file=" + str(temp_file),
                "--single-transaction",
            ]

            env = os.environ.copy()
            if db_password:
                env["PGPASSWORD"] = db_password
            else:
                print("⚠️ ПАРОЛЬ НЕ ПЕРЕДАН!")

            result = subprocess.run(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=600
            )

            print(f"📋 Результат: {result.returncode}")
            if result.stderr:
                print(f"📋 STDERR: {result.stderr[:500]}")

            if temp_file.exists():
                temp_file.unlink()

            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка восстановления: {result.stderr}"
                )

            return {
                "status": "success",
                "message": f"✅ БД успешно восстановлена из: {filename}"
            }

        except subprocess.TimeoutExpired:
            if temp_file.exists():
                temp_file.unlink()
            raise HTTPException(status_code=500, detail="Превышено время восстановления (10 минут)")
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/download/{filename}")
async def download_backup(filename: str):
    """Скачивает файл бэкапа"""
    filepath = BACKUP_DIR / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/gzip"
    )


@router.delete("/delete/{filename}")
async def delete_backup(filename: str):
    """Удаляет файл бэкапа"""
    filepath = BACKUP_DIR / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    filepath.unlink()

    return {
        "status": "success",
        "message": f"Бэкап {filename} удалён"
    }


@router.get("/list")
async def list_backups():
    """Возвращает список бэкапов в JSON"""
    return {
        "backups": get_backups_list(),
        "count": len(get_backups_list())
    }
