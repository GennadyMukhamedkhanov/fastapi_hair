from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.models.hairs import HairProduct, ProductStatusEnum
from app.v1.repositories.common import CommonRepository
from app.v1.repositories.helpers import get_product_or_404
from app.v1.schemas.products import ProductCreateSchema, ProductUpdateSchema


class ProductRepository(CommonRepository):
    model = HairProduct

    async def get_all_products(self, session: AsyncSession, status_list: list) -> list[HairProduct]:
        """Получает список всех товаров"""
        if status_list:
            stmt = select(self.model).where(or_(*status_list)).options(selectinload(self.model.tone))
        else:
            stmt = select(self.model).options(selectinload(self.model.tone))
        result = await session.execute(stmt)
        products = result.scalars().all()

        return products

    async def get_product(self, session: AsyncSession, product_id: int) -> HairProduct:
        """Получает товар по ID или 404"""
        product = await get_product_or_404(session, product_id)
        return product

    async def create_product(self, session: AsyncSession, data: ProductCreateSchema) -> HairProduct:
        """Создает новый товар"""

        # Проверяем уникальность tone+length
        stmt = (
            select(self.model)
            .where(self.model.tone_id == data.tone_id,
                   self.model.length_cm == data.length_cm
                   ))
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Продукт с таким тоном и длиной уже существует")

        product = self.model(
            **data.model_dump(),
            status=ProductStatusEnum.WAREHOUSE.value
        )
        session.add(product)
        await session.commit()
        await session.refresh(product, ['tone'])
        return product

    async def update_product(self, session: AsyncSession, product_id: int, data: ProductUpdateSchema) -> HairProduct:
        """ Обновление товара"""

        product = await get_product_or_404(session, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Продукт не найден")

        update_data = data.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in update_data.items():
            setattr(product, key, value)

        await session.commit()
        await session.refresh(product)
        return product

    #
    # async def get_products_list(
    #         self,
    #         db: AsyncSession,
    #         page: int,
    #         page_size: int,
    #         filters: ProductFilterParamsSchema,
    #         sort_params: SortParams
    # ) -> dict:
    #     """Получает список товаров с пагинацией"""
    #     stmt_total = select(func.count(HairProduct.id))
    #     stmt_products = select(HairProduct)
    #
    #     # Фильтры
    #     if filters.tone_id:
    #         stmt_total = stmt_total.where(HairProduct.tone_id == filters.tone_id)
    #         stmt_products = stmt_products.where(HairProduct.tone_id == filters.tone_id)
    #
    #     if filters.length_cm:
    #         stmt_total = stmt_total.where(HairProduct.length_cm == filters.length_cm)
    #         stmt_products = stmt_products.where(HairProduct.length_cm == filters.length_cm)
    #
    #     if filters.in_stock_only:
    #         stmt_total = stmt_total.where(HairProduct.stock_grams > 0)
    #         stmt_products = stmt_products.where(HairProduct.stock_grams > 0)
    #
    #     if filters.min_stock:
    #         stmt_total = stmt_total.where(HairProduct.stock_grams >= filters.min_stock)
    #         stmt_products = stmt_products.where(HairProduct.stock_grams >= filters.min_stock)
    #
    #     # Total count
    #     result = await db.execute(stmt_total)
    #     total = result.scalar() or 0
    #
    #     # Корректируем страницу
    #     page = max(1, min(page, (total // page_size) + 1)) if total > 0 else 1
    #
    #     # Продукты с сортировкой
    #     sort_field = getattr(HairProduct, sort_params.sort_by, HairProduct.created_at)
    #     sort_order = desc(sort_field) if sort_params.sort_order == "desc" else sort_field
    #
    #     stmt_products = stmt_products.order_by(sort_order) \
    #         .offset((page - 1) * page_size) \
    #         .limit(page_size)
    #
    #     result = await db.execute(stmt_products)
    #     products = result.scalars().all()
    #
    #     return {
    #         "items": products,
    #         "total": total,
    #         "page": page,
    #         "page_size": page_size,
    #         "pages": (total + page_size - 1) // page_size if page_size > 0 else 0
    #     }
