# from app.v1.repositories.orders import OrderRepository
from app.v1.repositories.products import ProductRepository

from typing import Annotated
from fastapi import Form
from decimal import Decimal

from app.v1.repositories.tones import HairToneRepository
from app.v1.schemas.products import ProductCreateSchema


async def get_product_repository() -> ProductRepository:
    return ProductRepository()


#
# async def get_order_repository() -> OrderRepository:
#     return OrderRepository()


def get_hair_tone_repository() -> HairToneRepository:
    return HairToneRepository()


async def product_create_form(
        tone_id: Annotated[int, Form(...)],
        length_cm: Annotated[int, Form(...)],
        purchase_price_per_100g: Annotated[Decimal, Form(...)],
        sale_price_per_100g: Annotated[Decimal, Form(...)],
        tax_rate: float = Form(0.0)
) -> ProductCreateSchema:
    return ProductCreateSchema(
        tone_id=tone_id,
        length_cm=length_cm,
        purchase_price_per_100g=purchase_price_per_100g,
        sale_price_per_100g=sale_price_per_100g,
        tax_rate=tax_rate,
    )
