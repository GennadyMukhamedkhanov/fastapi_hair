from decimal import Decimal
from enum import Enum
from typing import List

from sqlalchemy import String, Float, Integer, ForeignKey, Boolean, DateTime, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.database import Base


class ProductStatus(str, Enum):
    """Статусы товара для отслеживания его местонахождения"""
    WAREHOUSE = "warehouse"  # Товар находится на складе
    TRANSIT = "transit"  # Товар в пути к покупателю
    SOLD = "sold"  # Товар продан, у покупателя
    RETURN_TRANSIT = "return_transit"  # Товар возвращается на склад


class HairTone(Base):
    __tablename__ = "hair_tones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment="ID тона")
    tone: Mapped[str] = mapped_column(String(10), unique=True, index=True, comment="Код тона (6.0, 6.35, 8.13)")
    photo_url: Mapped[str] = mapped_column(String, nullable=True, comment="URL главной фото тона")

    products: Mapped[List["HairProduct"]] = relationship("HairProduct", back_populates="tone")


class HairProduct(Base):
    __tablename__ = "hair_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment="ID товара (тон+длина)")
    tone_id: Mapped[int] = mapped_column(ForeignKey("hair_tones.id"), index=True, comment="ID тона")
    length_cm: Mapped[int] = mapped_column(Integer, index=True, comment="Длина см (60, 70, 80...)")
    purchase_price_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), comment="Цена закупки за 100г")
    sale_price_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), comment="Оптимальная цена продажи за 100г")
    tax_rate: Mapped[float] = mapped_column(Float, default=0.0, comment="Налог (0.2=20%)")
    stock_grams: Mapped[int] = mapped_column(Integer, default=0, comment="Запас грамм")
    status: Mapped[ProductStatus] = mapped_column(String(20), default=ProductStatus.WAREHOUSE, comment="warehouse/transit/sold/return_transit")
    booking: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True, comment="Бронь до даты")

    # Связь с тоном
    tone: Mapped["HairTone"] = relationship("HairTone", back_populates="products")