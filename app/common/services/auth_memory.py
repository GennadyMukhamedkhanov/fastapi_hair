# app/common/services/auth_memory.py
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets
import json
from typing import Optional
import redis.asyncio as redis

from app.common.config import settings


@dataclass
class VerifyRecord:
    code: str
    expires_at: datetime
    attempts_left: int

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "expires_at": self.expires_at.isoformat(),
            "attempts_left": self.attempts_left
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VerifyRecord":
        return cls(
            code=data["code"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            attempts_left=data["attempts_left"]
        )


class AuthMemoryStore:
    def __init__(self) -> None:
        self._redis: redis.Redis | None = None
        print(f"🔧 AuthMemoryStore initialized, redis client: {self._redis}")

    # app/common/services/auth_memory.py
    async def init_redis(self) -> None:
        """Инициализация подключения к Redis"""
        # Формируем URL с паролем если он есть
        if settings.redis_password:
            redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        else:
            redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"

        print(f"🔄 Connecting to Redis at {settings.redis_host}:{settings.redis_port}")

        try:
            self._redis = await redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # Проверяем соединение
            await self._redis.ping()
            print("✅ Redis connected successfully")

        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            self._redis = None
            raise

    async def close_redis(self) -> None:
        """Закрытие подключения к Redis"""
        if self._redis:
            await self._redis.close()
            print("❌ Redis disconnected")
        else:
            print("⚠️ Redis already None, nothing to close")

    def _get_redis_key(self, email: str) -> str:
        return f"auth:code:{email.lower()}"

    async def generate_code(self, email: str) -> str:
        """Генерация и сохранение кода подтверждения"""
        print(f"📝 generate_code called for {email}")
        print(f"   Redis client exists: {self._redis is not None}")

        if not self._redis:
            print("❌ Redis client is None in generate_code!")
            raise RuntimeError("Redis not initialized")

        code = str(secrets.randbelow(900000) + 100000)
        print(f"   Generated code: {code}")

        record = VerifyRecord(
            code=code,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.verify_code_ttl_minutes),
            attempts_left=settings.verify_max_attempts,
        )

        key = self._get_redis_key(email)
        ttl_seconds = settings.verify_code_ttl_minutes * 60
        await self._redis.setex(key, ttl_seconds, json.dumps(record.to_dict()))
        print(f"✅ Code saved to Redis with key: {key}, TTL: {ttl_seconds}s")

        return code

    async def verify_code(self, email: str, code: str) -> tuple[bool, str]:
        """Проверка кода подтверждения"""
        print(f"🔍 verify_code called for {email}")
        print(f"   Redis client exists: {self._redis is not None}")

        if not self._redis:
            print("❌ Redis client is None in verify_code!")
            return False, "Redis не инициализирован"

        key = self._get_redis_key(email)
        print(f"   Looking up key: {key}")

        data = await self._redis.get(key)
        print(f"   Data from Redis: {data}")

        if not data:
            return False, "Код не найден. Запросите новый."

        try:
            record_dict = json.loads(data)
            record = VerifyRecord.from_dict(record_dict)
            print(f"   Restored record for {email}, attempts left: {record.attempts_left}")
        except Exception as e:
            print(f"   Error parsing data: {e}")
            return False, "Ошибка формата данных"

        now = datetime.now(timezone.utc)
        if now > record.expires_at:
            await self._redis.delete(key)
            print(f"   Code expired for {email}")
            return False, "Срок действия кода истёк."

        if record.attempts_left <= 0:
            await self._redis.delete(key)
            print(f"   No attempts left for {email}")
            return False, "Превышено количество попыток."

        if record.code != code:
            record.attempts_left -= 1
            print(f"   Wrong code for {email}. Attempts left: {record.attempts_left}")

            if record.attempts_left > 0:
                ttl = await self._redis.ttl(key)
                if ttl > 0:
                    await self._redis.setex(key, ttl, json.dumps(record.to_dict()))
                    print(f"   Updated record in Redis, new attempts: {record.attempts_left}")
            else:
                await self._redis.delete(key)
                print(f"   Deleted record, no attempts left")

            return False, f"Неверный код. Осталось попыток: {record.attempts_left}"

        await self._redis.delete(key)
        print(f"✅ Code verified and deleted for {email}")
        return True, "OK"

    async def get_code_info(self, email: str) -> Optional[dict]:
        if not self._redis:
            return None

        key = self._get_redis_key(email)
        data = await self._redis.get(key)

        if not data:
            return None

        try:
            record_dict = json.loads(data)
            record = VerifyRecord.from_dict(record_dict)
            ttl = await self._redis.ttl(key)

            return {
                "email": email,
                "code": record.code,
                "expires_at": record.expires_at.isoformat(),
                "attempts_left": record.attempts_left,
                "ttl_seconds": ttl
            }
        except Exception:
            return None

    # ============================================
    #  МЕТОДЫ ДЛЯ СКЛАДОВ
    # ============================================

    async def get_warehouse_data(self) -> dict:
        """
        Получить данные складов из Redis
        """
        if not self._redis:
            print("⚠️ Redis не инициализирован, возвращаем пустые данные")
            return {}

        try:
            data = await self._redis.get("warehouse_data")
            if data:
                return json.loads(data)
            return {}
        except Exception as e:
            print(f"❌ Ошибка получения данных складов: {e}")
            return {}

    async def save_warehouse_data(self, data: dict) -> bool:
        """
        Сохранить все данные складов в Redis
        """
        if not self._redis:
            print("⚠️ Redis не инициализирован, данные не сохранены")
            return False

        try:
            await self._redis.set("warehouse_data", json.dumps(data))
            print(f"✅ Данные складов сохранены в Redis: {len(data)} позиций")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения данных складов: {e}")
            return False

    async def save_warehouse_row(self, product_id: int, dmitrieva: int, zelenaya: int) -> bool:
        """
        Сохранить данные по одному товару в Redis
        """
        if not self._redis:
            print("⚠️ Redis не инициализирован")
            return False

        try:
            # Загружаем текущие данные
            current = await self.get_warehouse_data()

            # Обновляем
            current[str(product_id)] = {
                "dmitrieva": dmitrieva,
                "zelenaya": zelenaya
            }

            # Сохраняем
            return await self.save_warehouse_data(current)
        except Exception as e:
            print(f"❌ Ошибка сохранения строки складов: {e}")
            return False

    async def clear_warehouse_data(self) -> bool:
        """
        Очистить все данные складов в Redis
        """
        if not self._redis:
            return False

        try:
            await self._redis.delete("warehouse_data")
            print("✅ Данные складов очищены")
            return True
        except Exception as e:
            print(f"❌ Ошибка очистки данных складов: {e}")
            return False


auth_memory_store = AuthMemoryStore()


