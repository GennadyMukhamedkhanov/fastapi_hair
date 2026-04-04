from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import Field, ConfigDict, model_validator, BaseModel

from app.v1.enums import ProductStatusEnum
from app.v1.schemas.base import PaginationResponse
from app.v1.schemas.tones import HairToneOutSchema


class ProductCreateSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=lambda x: x[0].upper() + x[1:])

    tone_id: Annotated[int, Field(gt=0, description="ID оттенка волос")]
    length_cm: Annotated[int, Field(ge=10, le=100, description="Длина волос в см")]
    purchase_price_per_100g: Annotated[Decimal, Field(decimal_places=2, gt=0, description="Закупочная цена за 100г")]
    sale_price_per_100g: Annotated[Decimal, Field(decimal_places=2, gt=0, description="Цена продажи за 100г")]
    tax_rate: Annotated[float, Field(default=0.0, ge=0.0, le=1.0, description="Налоговая ставка")]


class ProductUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    purchase_price_per_100g: Annotated[
        Optional[Decimal], Field(None, decimal_places=2, gt=0, description="Новая закупочная цена")]
    sale_price_per_100g: Annotated[
        Optional[Decimal], Field(None, decimal_places=2, gt=0, description="Новая цена продажи")]
    tax_rate: Annotated[Optional[float], Field(None, ge=0.0, le=1.0, description="Новая налоговая ставка")]
    stock_grams: Annotated[Optional[int], Field(None, ge=0, description="Новый остаток на складе")]

    @model_validator(mode="after")
    def validate_prices(self):
        if (
                self.purchase_price_per_100g is not None
                and self.sale_price_per_100g is not None
                and self.purchase_price_per_100g >= self.sale_price_per_100g
        ):
            raise ValueError("Закупочная цена должна быть меньше цены продажи")
        return self


class ProductStatusSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    warehouse: Annotated[bool, Field(False, description="Фильтр по складу")]
    transit: Annotated[bool, Field(False, description="Фильтр по товару в пути")]
    delivered: Annotated[bool, Field(False, description="Фильтр по доставленному товару, проданому")]
    return_transit: Annotated[bool, Field(False, description="Фильтр по возвращенному товару")]


class ProductOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True,
                              alias_generator=lambda x: x[0].upper() + x[1:])

    id: Annotated[int, Field(description="ID товара")]
    tone: Annotated[HairToneOutSchema, Field(description="Оттенок волос")]
    length_cm: Annotated[int, Field(description="Длина в см")]
    purchase_price_per_100g: Annotated[Decimal, Field(description="Закупочная цена за 100г")]
    sale_price_per_100g: Annotated[Decimal, Field(description="Цена продажи за 100г")]
    tax_rate: Annotated[float, Field(description="Налоговая ставка")]
    stock_grams: Annotated[int, Field(description="Остаток на складе")]
    status: Annotated[ProductStatusEnum, Field(description="Статус товара")]
    booking: Annotated[Optional[datetime], Field(None, description="Дата бронирования")]


ProductListResponse = PaginationResponse[ProductOutSchema]


class ProductStockUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    delta_grams: Annotated[int, Field(description="Дельта изменения остатков (+приход, -расход)")]
