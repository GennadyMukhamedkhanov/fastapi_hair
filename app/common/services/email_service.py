import ssl
import logging
from email.message import EmailMessage
import aiosmtplib
from app.common.config import settings

logger = logging.getLogger(__name__)


async def send_verification_code(email: str, code: str) -> None:
    tls_context = ssl.create_default_context()

    if settings.app_env == "dev":
        tls_context.check_hostname = False
        tls_context.verify_mode = ssl.CERT_NONE
        logger.warning("⚠️ SSL verification disabled for development environment")

    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = email
    message["Subject"] = "Код подтверждения входа"
    message.set_content(
        f"Ваш код подтверждения: {code}\n\n"
        f"Код действует {settings.verify_code_ttl_minutes} минут.\n\n"
        f"Если вы не запрашивали код, проигнорируйте это сообщение."
    )

    client = aiosmtplib.SMTP(
        hostname=settings.mail_smtp_host,
        port=settings.mail_smtp_port,
        use_tls=False,
        start_tls=False,
        timeout=15,
    )

    try:
        await client.connect()
        await client.starttls(
            tls_context=tls_context,
            validate_certs=False if settings.app_env == "dev" else True,
        )
        await client.login(settings.mail_smtp_user, settings.mail_smtp_password)
        await client.send_message(message)
        logger.info(f"✅ Код подтверждения отправлен на {email}")

    except aiosmtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ SMTP auth error: {e}")
        raise RuntimeError("Неверный логин или пароль SMTP")

    except aiosmtplib.SMTPException as e:
        logger.error(f"❌ SMTP error: {e}")
        raise RuntimeError(f"SMTP ошибка: {e}")

    except Exception as e:
        logger.error(f"❌ Email send error: {e}")
        raise RuntimeError(f"Не удалось отправить email: {e}")

    finally:
        try:
            await client.quit()
        except Exception:
            pass