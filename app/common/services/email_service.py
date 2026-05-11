from email.message import EmailMessage
import aiosmtplib

from app.common.config import settings


async def send_verification_code(email: str, code: str) -> None:
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = email
    message["Subject"] = "Код подтверждения входа"
    message.set_content(
        f"Ваш код подтверждения: {code}\n\n"
        f"Код действует {settings.verify_code_ttl_minutes} минут."
    )

    await aiosmtplib.send(
        message,
        hostname=settings.mail_smtp_host,
        port=settings.mail_smtp_port,
        start_tls=True,
        username=settings.mail_smtp_user,
        password=settings.mail_smtp_password,
    )

