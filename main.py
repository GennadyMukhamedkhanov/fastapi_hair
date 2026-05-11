import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.v1.main import app_v1
from app.common.services.auth_memory import auth_memory_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting up main app...")
    await auth_memory_store.init_redis()
    print("✅ Auth memory store initialized with Redis")

    yield

    # Shutdown
    print("🛑 Shutting down main app...")
    await auth_memory_store.close_redis()
    print("❌ Auth memory store closed")


# Создаём основное приложение с lifespan
app = FastAPI(
    title="CRM hair API",
    version="1.0.0",
    lifespan=lifespan  # Добавляем lifespan здесь
)

# Монтируем версии
app.mount("/v1", app_v1)


# Корневой эндпоинт с информацией о версиях
@app.get("/")
async def root():
    return {
        "message": "Добро пожаловать в API CRM hair!",
        "versions": {
            "v1": "/v1/docs",
            "v2": "/v2/docs (на данный момент не работает)",
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )