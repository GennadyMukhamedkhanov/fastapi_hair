from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.database import Base
from app.v1.enums import ProductStatusEnum



class HairTone(Base):
    __tablename__ = "hair_tones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment="Уникальный идентификатор оттенка волос")
    tone: Mapped[str] = mapped_column(String(10), unique=True, index=True, comment="Код или название оттенка волос")
    photo_url: Mapped[str] = mapped_column(String, nullable=True, comment="Ссылка на изображение, показывающее данный оттенок волос")

    products: Mapped[List["HairProduct"]] = relationship("HairProduct", back_populates="tone")


class HairProduct(Base):
    __tablename__ = "hair_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment="Уникальный идентификатор товара")
    tone_id: Mapped[int] = mapped_column(ForeignKey("hair_tones.id"), index=True, comment="Ссылка на оттенок, к которому относится товар")
    length_cm: Mapped[int] = mapped_column(Integer, index=True, comment="Длина волос в сантиметрах")
    purchase_price_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), comment="Текущая закупочная цена товара за 100 грамм")
    sale_price_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0.0, comment="Текущая цена продажи товара за 100 грамм")
    tax_rate: Mapped[float] = mapped_column(Float, default=0.0, comment="Налоговая ставка, применяемая к товару")
    stock_grams: Mapped[int] = mapped_column(Integer, default=0, comment="Текущий остаток товара на складе в граммах")
    status: Mapped[str] = mapped_column(String(20), default=ProductStatusEnum.WAREHOUSE.value, comment="Текущий статус товара в системе")
    booking: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="Дата и время бронирования товара, если он зарезервирован")

    tone: Mapped["HairTone"] = relationship("HairTone", back_populates="products")

