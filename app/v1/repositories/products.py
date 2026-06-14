from fastapi import HTTPException
from sqlalchemy import select, or_, and_
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
                   self.model.length_cm == data.length_cm)
        )
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
        result = await session.execute(
            select(self.model)
            .where(self.model.id == product.id)
            .options(selectinload(self.model.tone))
        )
        product_with_tone = result.scalar_one()

        return product_with_tone

    async def update_product(self, session: AsyncSession, product_id: int, data: ProductUpdateSchema) -> HairProduct:
        """ Обновление товара с пересчетом средней цены при добавлении"""

        product = await get_product_or_404(session, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Продукт не найден")

        # Получаем текущие значения
        old_stock_grams = product.stock_grams
        old_purchase_price_per_100g = product.purchase_price_per_100g

        # Подготавливаем данные для обновления (только переданные поля)
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)

        # Проверяем: изменилось ли количество и цена закупки
        new_stock_grams = update_data.get('stock_grams')
        new_purchase_price_per_100g = update_data.get('purchase_price_per_100g')

        # СЛУЧАЙ 1: Количество было 0 - просто обновляем
        if old_stock_grams == 0:
            for key, value in update_data.items():
                setattr(product, key, value)

            await session.commit()
            await session.refresh(product)
            return product

        # СЛУЧАЙ 2: Добавляем товар к существующему (нужен пересчет цены)
        elif new_stock_grams and new_stock_grams > old_stock_grams:
            added_grams = new_stock_grams - old_stock_grams

            # Если передана новая цена закупки - используем её для пересчета
            if new_purchase_price_per_100g:
                # Вычисляем среднюю цену
                old_total_value = (old_purchase_price_per_100g / 100) * old_stock_grams
                new_total_value = (new_purchase_price_per_100g / 100) * added_grams
                total_value = old_total_value + new_total_value
                total_grams = old_stock_grams + added_grams

                # Средняя цена за 100 грамм
                avg_price_per_100g = (total_value / total_grams) * 100

                # Обновляем поля
                update_data['purchase_price_per_100g'] = round(avg_price_per_100g, 2)
                update_data['stock_grams'] = new_stock_grams
            else:
                # Если цена не передана, используем старую цену
                update_data['stock_grams'] = new_stock_grams

            # Применяем обновления
            for key, value in update_data.items():
                setattr(product, key, value)

        # СЛУЧАЙ 3: Уменьшаем количество (продажа, списание)
        elif new_stock_grams and new_stock_grams < old_stock_grams:
            # Цена не пересчитывается, просто уменьшаем остаток
            update_data['stock_grams'] = new_stock_grams

            for key, value in update_data.items():
                setattr(product, key, value)

        # СЛУЧАЙ 4: Обновляем только цену без изменения количества
        elif new_purchase_price_per_100g and not new_stock_grams:
            # Просто обновляем цену для всего остатка
            setattr(product, 'purchase_price_per_100g', new_purchase_price_per_100g)

        # СЛУЧАЙ 5: Обновляем другие поля (налог, цену продажи и т.д.)
        else:
            for key, value in update_data.items():
                setattr(product, key, value)

        await session.commit()
        await session.refresh(product)
        return product

    async def get_products_available_for_order(self, session: AsyncSession) -> list[HairProduct]:
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.status == ProductStatusEnum.WAREHOUSE.value,
                    self.model.stock_grams > 0,
                )
            )
            .options(selectinload(self.model.tone))
        )
        result = await session.execute(stmt)
        return result.scalars().all()
