from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models import HairProduct, Order


async def get_product_or_404(session: AsyncSession, product_id: int) -> HairProduct:
    stmt = select(HairProduct).where(HairProduct.id == product_id).options(selectinload(HairProduct.tone))
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


async def get_order_or_404(session: AsyncSession, order_id: int) -> Order:
    order = await session.get(Order, order_id)
    if not order or order.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


async def generate_order_number(session: AsyncSession) -> str:
    year = datetime.now().year
    result = await session.execute(
        select(func.count(Order.id)).where(func.extract("year", Order.created_at) == year)
    )
    seq = (result.scalar_one() or 0) + 1
    return f"ORD-{year}-{seq:05d}"


def get_list_status(warehouse, transit, delivered, return_transit):
    status_list = []

    if warehouse:
        status_list.append(HairProduct.status == 'warehouse')

    if transit:
        status_list.append(HairProduct.status == 'transit')

    if delivered:
        status_list.append(HairProduct.status == 'delivered')

    if return_transit:
        status_list.append(HairProduct.status == 'return_transit')

    return status_list
