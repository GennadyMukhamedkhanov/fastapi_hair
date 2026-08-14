# app/tasks/send_email.py

from app.celery_app import celery_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.send_email.send_email_client')
def send_email_client(recipient: str, text: str):
    """
    Задача по отправке сообщения (заглушка)
    """
    logger.info(f"📨 Отправка сообщения получателю: {recipient}")
    logger.info(f"📝 Текст: {text}")
    logger.info(f"⏰ Время отправки: {datetime.now()}")

    return {
        "status": "success",
        "recipient": recipient,
        "message": text,
        "sent_at": str(datetime.now())
    }
