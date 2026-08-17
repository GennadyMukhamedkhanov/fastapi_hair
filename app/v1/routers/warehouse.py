# app/v1/routers/warehouse.py
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.v1.conf.templates import templates
from app.v1.schemas.warehouse import ProductWarehouseSchema
from app.common.services.auth_memory import auth_memory_store
from app.v1.services.orders import get_create_order_page_service

router = APIRouter(tags=["warehouse"])


@router.get("/", response_class=HTMLResponse, name="warehouse_page")
async def get_page_stock_warehouse(
        request: Request,
        data: dict = Depends(get_create_order_page_service)
):
    """Возвращает страницу для сверки товаров на складах"""
    products = [ProductWarehouseSchema.model_validate(p).model_dump() for p in data["products"]]

    return templates.TemplateResponse(
        request=request,
        name="warehouse.html",
        context={
            "products": products
        }
    )


@router.get("/data")
async def get_warehouse_data():
    """
    Получить все данные складов из Redis
    Использует существующее подключение auth_memory_store
    """
    try:
        data = await auth_memory_store.get_warehouse_data()
        return data
    except Exception as e:
        print(f"❌ Ошибка получения данных из Redis: {e}")
        return {}


@router.post("/save")
async def save_warehouse_row(data: dict):
    """
    Сохранить данные по одному товару в Redis
    """
    product_id = data.get("product_id")
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id required")

    try:
        success = await auth_memory_store.save_warehouse_row(
            product_id=product_id,
            dmitrieva=data.get("dmitrieva", 0),
            zelenaya=data.get("zelenaya", 0)
        )

        if success:
            return {"status": "success", "message": f"Product {product_id} saved"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save to Redis")

    except Exception as e:
        print(f"❌ Ошибка сохранения в Redis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-all")
async def save_warehouse_all(data: dict):
    """
    Сохранить все данные складов в Redis
    """
    try:
        success = await auth_memory_store.save_warehouse_data(data)

        if success:
            return {"status": "success", "message": "All data saved"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save to Redis")

    except Exception as e:
        print(f"❌ Ошибка сохранения в Redis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_warehouse_data():
    """
    Очистить все данные складов в Redis
    """
    try:
        success = await auth_memory_store.clear_warehouse_data()

        if success:
            return {"status": "success", "message": "All warehouse data cleared"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear Redis data")

    except Exception as e:
        print(f"❌ Ошибка очистки Redis: {e}")
        raise HTTPException(status_code=500, detail=str(e))