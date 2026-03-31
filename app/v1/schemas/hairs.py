from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


class HairToneSchema(BaseModel):
    id: Annotated[int, Field(..., description="ID позиции корзины")]
    tone: Annotated[str, Field(..., description="Код тона волос (например: 6.0, 6.35, 8.13 - уникальный)")]

    model_config = ConfigDict(from_attributes=True)


class CreateHairToneSchema(BaseModel):
    tone: Annotated[str, Field(..., description="Код тона волос (например: 6.0, 6.35, 8.13 - уникальный)")]



class HairProductCreate(BaseModel):
    tone_id: Annotated[int, Field(description="ID тона", ge=0)]
    length_cm: Annotated[int, Field(description="Длина см (60, 70, 80...)", ge=0)]
    purchase_price_per_100g: Annotated[float, Field(description="Цена закупки за 100г", ge=0)]
    sale_price_per_100g: Annotated[float, Field(description="Оптимальная цена продажи за 100г", ge=0)]
    stock_grams: Annotated[int, Field(description="Колличество волос в граммах", ge=0)]

