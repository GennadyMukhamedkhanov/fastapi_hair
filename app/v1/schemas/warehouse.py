from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============================================
# БАЗОВЫЕ СХЕМЫ
# ============================================

class HairToneSchema(BaseModel):
    """Схема тона волос"""
    id: int = Field(..., description="ID тона")
    tone: str = Field(..., description="Название тона")
    photo_url: Optional[str] = Field(None, description="URL фото тона")

    class Config:
        from_attributes = True


class ProductBaseSchema(BaseModel):
    """Базовая схема товара"""
    id: int = Field(..., description="ID товара")
    length_cm: int = Field(..., description="Длина в см", ge=0)
    purchase_price_per_100g: float = Field(..., description="Цена закупки за 100г", ge=0)
    sale_price_per_100g: float = Field(..., description="Цена продажи за 100г", ge=0)
    tax_rate: float = Field(0.0, description="Налоговая ставка", ge=0, le=100)
    stock_grams: int = Field(0, description="Остаток на складе в граммах", ge=0)
    status: str = Field(..., description="Статус товара")
    booking: Optional[datetime] = Field(None, description="Бронирование")


class ProductWarehouseSchema(ProductBaseSchema):
    """Схема товара для страницы сверки складов"""
    tone: Optional[HairToneSchema] = Field(None, description="Тон волос")

    class Config:
        from_attributes = True


# ============================================
# СХЕМЫ ДЛЯ СВЕРКИ СКЛАДОВ
# ============================================

class WarehouseItemSchema(BaseModel):
    """Схема для одного склада"""
    dmitrieva: int = Field(0, description="Склад Дмитриева (граммы)", ge=0)
    zelenaya: int = Field(0, description="Склад Зеленая (граммы)", ge=0)


class ProductWarehouseDataSchema(BaseModel):
    """Схема товара с данными складов"""
    product_id: int = Field(..., description="ID товара")
    product: ProductWarehouseSchema = Field(..., description="Данные товара")
    warehouse: WarehouseItemSchema = Field(..., description="Данные складов")
    total: int = Field(..., description="Сумма по складам")
    is_match: bool = Field(..., description="Совпадает ли с остатком")


class ProductWarehouseSaveSchema(BaseModel):
    """Схема для сохранения данных складов"""
    product_id: int = Field(..., description="ID товара")
    dmitrieva: int = Field(0, description="Склад Дмитриева (граммы)", ge=0)
    zelenaya: int = Field(0, description="Склад Зеленая (граммы)", ge=0)


# ============================================
# СХЕМЫ ДЛЯ API ОТВЕТОВ
# ============================================

class WarehouseDataResponseSchema(BaseModel):
    """Ответ с данными складов"""
    data: dict[int, WarehouseItemSchema] = Field(default_factory=dict, description="Данные по товарам")
    total_items: int = Field(0, description="Всего позиций")
    mismatches: int = Field(0, description="Количество несовпадений")


class WarehouseSaveResponseSchema(BaseModel):
    """Ответ на сохранение"""
    status: str = Field(..., description="Статус операции")
    message: str = Field(..., description="Сообщение")
    saved_count: int = Field(0, description="Количество сохраненных позиций")


# ============================================
# СХЕМЫ ДЛЯ СТАТИСТИКИ
# ============================================

class WarehouseStatsSchema(BaseModel):
    """Статистика сверки"""
    total_products: int = Field(..., description="Всего товаров")
    total_stock: int = Field(..., description="Общий остаток")
    total_dmitrieva: int = Field(..., description="Итого на Дмитриева")
    total_zelenaya: int = Field(..., description="Итого на Зеленая")
    total_sum: int = Field(..., description="Сумма по складам")
    mismatch_count: int = Field(0, description="Количество несовпадений")
    is_match: bool = Field(..., description="Всё совпадает")