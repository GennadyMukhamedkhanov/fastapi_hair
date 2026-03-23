from decimal import Decimal
from enum import Enum
from typing import List

from sqlalchemy import String, Float, Integer, ForeignKey, Boolean, DateTime, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProductStatus(str, Enum):
    """Статусы товара для отслеживания его местонахождения"""
    WAREHOUSE = "warehouse"      # Товар находится на складе
    TRANSIT = "transit"          # Товар в пути к покупателю
    SOLD = "sold"                # Товар продан, у покупателя
    RETURN_TRANSIT = "return_transit"  # Товар возвращается на склад

class HairTone(Base):
    __tablename__ = "hair_tones"

    # Уникальный ID тона волос (автоинкремент)
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный ID тона волос (автоинкремент)"
    )

    # Код тона волос (например: "6.0", "6.35", "8.13" - уникальный)
    tone: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        index=True,
        comment="Код тона волос (например: 6.0, 6.35, 8.13 - уникальный)"
    )

    # Связь: продукты этого тона (один тон - много длин/позиций)
    products: Mapped[List["HairProduct"]] = relationship(back_populates="tone")

    # Связь: фотографии этого тона (один тон - много фото)
    photos: Mapped[List["HairPhoto"]] = relationship(back_populates="tone")

class HairProduct(Base):
    __tablename__ = "hair_products"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный ID товара (тон+длина = уникальная позиция)"
    )

    tone_id: Mapped[int] = mapped_column(
        ForeignKey("hair_tones.id"),
        index=True,
        comment="ID связанного тона волос (ForeignKey на hair_tones)"
    )

    length_cm: Mapped[int] = mapped_column(
        Integer,
        index=True,
        comment="Длина волос в сантиметрах (60, 70, 80, 90...)"
    )

    purchase_price_per_50g: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        comment="Цена закупки за 50 грамм (например: 1500.00 руб.)"
    )

    sale_price_per_50g: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        comment="Цена продажи за 50 грамм (например: 2500.00 руб.)"
    )

    tax_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="Ставка налога (доля: 0.2 = 20%, 0.13 = 13%)"
    )

    stock_grams: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Общий запас на складе в граммах (всегда >= 0)"
    )

    status: Mapped[ProductStatus] = mapped_column(
        String(20),
        default=ProductStatus.WAREHOUSE,
        comment="Текущее местонахождение товара (warehouse/transit/sold/return_transit)"
    )

    deleted_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=True,
        comment="Мягкое удаление - скрывает товар из списков (NULL=активен)"
    )

    # Связь: тон волос этого продукта (для JOIN запросов)
    tone: Mapped["HairTone"] = relationship(back_populates="products")

    # Связь: позиции заказов с этим продуктом
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="product")

class HairPhoto(Base):
    __tablename__ = "hair_photos"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Уникальный ID фотографии"
    )

    tone_id: Mapped[int] = mapped_column(
        ForeignKey("hair_tones.id"),
        comment="ID тона волос (ForeignKey на hair_tones)"
    )

    image_url: Mapped[str] = mapped_column(
        String,
        comment="URL изображения (путь к файлу: /static/photos/6.0-1.jpg)"
    )

    is_main: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Флаг главной фотографии тона (True=показывать первой)"
    )

    deleted_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=True,
        comment="Мягкое удаление фотографии (NULL=активна)"
    )

    # Связь: тон волос этой фотографии
    tone: Mapped["HairTone"] = relationship(back_populates="photos")

