from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, List, Optional

from pydantic import BaseModel
from pydantic import Field, ConfigDict

from app.v1.enums import OrderStatus


class OrderItemCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=lambda x: x[0].upper() + x[1:])

    product_id: Annotated[int, Field(gt=0, description="ID товара")]
    grams: Annotated[int, Field(ge=1, le=10000, description="Количество граммов")]


class OrderCreateSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=lambda x: x[0].upper() + x[1:])

    items: Annotated[List[OrderItemCreate], Field(..., min_items=1, description="Позиции заказа")]
    seller_id: Annotated[Optional[int], Field(None, gt=0, description="ID продавца")]


class OrderStatusUpdateSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: Annotated[OrderStatus, Field(description="Новый статус заказа")]
    final_price: Annotated[Optional[Decimal], Field(None, decimal_places=2, description="Финальная цена")]


class OrderItemOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True,
                              alias_generator=lambda x: x[0].upper() + x[1:])

    id: Annotated[int, Field(description="ID позиции")]
    product_id: Annotated[int, Field(description="ID товара")]
    grams: Annotated[int, Field(description="Граммы")]
    purchase_price_per_100g: Annotated[Decimal, Field(description="Закупочная цена за 100г")]
    sale_price_per_100g: Annotated[Decimal, Field(description="Цена продажи за 100г")]
    total_sale_price: Annotated[Decimal, Field(description="Итоговая сумма")]
    profit: Annotated[Decimal, Field(description="Прибыль по позиции")]


class OrderOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True,
                              alias_generator=lambda x: x[0].upper() + x[1:])

    id: Annotated[int, Field(description="ID заказа")]
    order_number: Annotated[str, Field(description="Номер заказа")]
    status: Annotated[OrderStatus, Field(description="Статус")]
    total_price: Annotated[Optional[Decimal], Field(None, description="Сумма до корректировок")]
    final_price: Annotated[Optional[Decimal], Field(None, description="Финальная сумма")]
    profit: Annotated[Optional[Decimal], Field(None, description="Общая прибыль")]
    seller_id: Annotated[Optional[int], Field(None, description="ID продавца")]
    created_at: Annotated[datetime, Field(description="Дата создания")]
    deleted_at: Annotated[Optional[datetime], Field(None, description="Дата удаления")]
    items: Annotated[List[OrderItemOutSchema], Field(description="Позиции заказа")]
