# app/celery_app.py

from celery import Celery
from celery.schedules import crontab
import os
from datetime import timedelta

# Настройки из переменных окружения
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_DB = os.getenv('REDIS_DB', '0')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# Формируем URL для подключения к Redis
if REDIS_PASSWORD:
    REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
else:
    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

# Создаем экземпляр Celery
celery_app = Celery(
    'fastapi_hair',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'app.tasks',  # Подключаем всю папку tasks
    ]
)

# Настройки Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    result_expires=3600,
)

# Настройка периодических задач (расписание)
celery_app.conf.beat_schedule = {
    'create_backup_db': {
        'task': 'app.tasks.backup_db.create_backup_db',
        'schedule': crontab(minute=0, hour=3),  # Каждый день в 3:00
    },
}
