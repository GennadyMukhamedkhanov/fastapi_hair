from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi import APIRouter, status, Depends

# Создаём маршрутизатор с префиксом и тегом
router = APIRouter(
    tags=["index"]
)


@router.get("/", response_class=HTMLResponse)
async def home():
    html_path = Path("app/v1/templates/index.html")
    return html_path.read_text(encoding="utf-8")
