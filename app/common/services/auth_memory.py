from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets

from app.common.config import settings


@dataclass
class VerifyRecord:
    code: str
    expires_at: datetime
    attempts_left: int


class AuthMemoryStore:
    def __init__(self) -> None:
        self._codes: dict[str, VerifyRecord] = {}

    def generate_code(self, email: str) -> str:
        code = str(secrets.randbelow(900000) + 100000)
        self._codes[email] = VerifyRecord(
            code=code,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.verify_code_ttl_minutes),
            attempts_left=settings.verify_max_attempts,
        )
        return code

    def verify_code(self, email: str, code: str) -> tuple[bool, str]:
        record = self._codes.get(email)

        if not record:
            return False, "Код не найден. Запросите новый."

        now = datetime.now(timezone.utc)
        if now > record.expires_at:
            self._codes.pop(email, None)
            return False, "Срок действия кода истёк."

        if record.attempts_left <= 0:
            self._codes.pop(email, None)
            return False, "Превышено количество попыток."

        if record.code != code:
            record.attempts_left -= 1
            return False, f"Неверный код. Осталось попыток: {record.attempts_left}"

        self._codes.pop(email, None)
        return True, "OK"


auth_memory_store = AuthMemoryStore()