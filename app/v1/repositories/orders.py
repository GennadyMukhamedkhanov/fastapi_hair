from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import select, func, case, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.models import Order, OrderItem
from app.common.models.hairs import HairProduct, HairTone
from app.v1.enums import ProductStatusEnum, OrderStatus
from app.v1.repositories.common import CommonRepository
from app.v1.schemas.orders import OrderCreateSchema


class OrderRepository(CommonRepository):
    model = Order

    async def get_orders(
            self,
            filters: list,
            session: AsyncSession,
            seller_id: int | None = None,

    ) -> list[Order]:

        status_order = case(
            {
                OrderStatus.IN_TRANSIT.value: 1,  # 'transit' - сначала
                OrderStatus.RETURN_TRANSIT.value: 2,  # 'return_transit' - затем
                OrderStatus.DELIVERED.value: 3,  # 'delivered' - потом
                OrderStatus.RETURNED_ON_WAREHOUSE.value: 4,  # 'returned_on_warehouse' -
                OrderStatus.DELETED.value: 5  # 'returned_on_warehouse' - в конце
            },
            value=Order.status,
            else_=6
        )
        stmt = (
            select(Order).where(or_(*filters))
            .options(
                selectinload(Order.items_rel).selectinload(OrderItem.product),
                selectinload(Order.seller),
            )
            .order_by(status_order, Order.created_at.desc(), Order.id.desc())
        )

        if seller_id is not None:
            stmt = stmt.where(Order.seller_id == seller_id)

        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    async def create_order(
            self,
            session: AsyncSession,
            order_data: OrderCreateSchema,
            user_name: str,
            delivery_service: str
    ) -> Order:
        if not order_data.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Заказ должен содержать хотя бы одну позицию",
            )

        merged_items: dict[int, int] = defaultdict(int)
        for item in order_data.items:
            merged_items[item.product_id] += item.grams

        product_ids = list(merged_items.keys())

        stmt = (
            select(HairProduct)
            .where(HairProduct.id.in_(product_ids))
            .options(selectinload(HairProduct.tone))
        )
        result = await session.execute(stmt)
        products = result.scalars().all()
        products_map = {product.id: product for product in products}

        missing_ids = [pid for pid in product_ids if pid not in products_map]
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Товары не найдены: {missing_ids}",
            )

        # при создании считаются только закупочные суммы (если нужны),
        # продажная цена и прибыль пока не считаются
        order_items: list[OrderItem] = []

        for product_id, grams in merged_items.items():
            product = products_map[product_id]

            if product.status != ProductStatusEnum.WAREHOUSE.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Товар {product_id} недоступен для заказа",
                )

            if grams > product.stock_grams:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Недостаточно остатка для товара {product.tone.tone} "
                        f"{product.length_cm} см. "
                        f"Доступно: {product.stock_grams} г, запрошено: {grams} г"
                    ),
                )

            # закупочная цена фиксируется при создании
            purchase_total = (
                    Decimal(grams) * product.purchase_price_per_100g / Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            order_item = OrderItem(
                product_id=product.id,
                grams=grams,
                purchase_price_per_100g=product.purchase_price_per_100g,
                sale_price_per_100g=Decimal("0.00"),  # или None, если колонка nullable
                total_sale_price=Decimal("0.00"),  # или None
                profit=Decimal("0.00"),  # или None
            )
            order_items.append(order_item)

            product.stock_grams -= grams

        # total_price / final_price / profit пока не заполняются,
        # или можно оставить как Decimal("0.00"), если хочешь избежать null
        order = Order(
            order_number=self._generate_order_number(user_name, delivery_service),
            status=OrderStatus.IN_TRANSIT.value,
            total_price=Decimal("0.00"),  # либо None, если поле nullable
            final_price=Decimal("0.00"),  # либо None
            profit=Decimal("0.00"),  # либо None
            seller_id=order_data.seller_id,
            items_rel=order_items,
        )

        session.add(order)
        await session.commit()
        await session.refresh(order)

        return await self.get_order_by_id(session=session, order_id=order.id)

    async def get_order_by_id(self, session: AsyncSession, order_id: int) -> Order | None:
        stmt = (
            select(self.model)
            .where(self.model.id == order_id)
            .options(
                selectinload(self.model.items_rel)
                .selectinload(OrderItem.product)
                .selectinload(HairProduct.tone),
                selectinload(self.model.seller),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_order_by_id_with_lock(self, session: AsyncSession, order_id: int) -> Order | None:
        stmt = (
            select(self.model)
            .where(self.model.id == order_id)
            .options(
                selectinload(self.model.items_rel)
                .selectinload(OrderItem.product)
                .selectinload(HairProduct.tone),
                selectinload(self.model.seller),
            )
            .with_for_update()  # Блокируем строку
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_sale_prices_on_delivery(
            self,
            session: AsyncSession,
            order_id: int,
            sale_prices: dict[int, Decimal],  # product_id → total_price (цена за позицию)
    ) -> Order:
        """Устанавливает цены продажи для товаров в заказе при доставке"""


        stmt = (
            select(self.model)
            .where(self.model.id == order_id)
            .options(selectinload(self.model.items_rel).selectinload(OrderItem.product))
        )
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        total_price = Decimal("0.00")
        total_profit = Decimal("0.00")

        # Перебираем все позиции в заказе
        for item in order.items_rel:
            product_id = item.product_id

            if product_id not in sale_prices:
                raise HTTPException(
                    status_code=400,
                    detail=f"Не указана цена продажи для товара '{item.product.name}'"
                )

            # Цена за позицию (введенная пользователем)
            sale_price_per_unit = sale_prices[product_id]

            # Рассчитываем цену за 100г для хранения в БД
            if item.grams > 0:
                sale_price_100g = (
                        sale_price_per_unit / Decimal(item.grams) * Decimal("100")
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                sale_price_100g = Decimal("0.00")

            # Итоговая сумма продажи (цена за позицию)
            sale_total = sale_price_per_unit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Вычисляем закупочную сумму
            purchase_total = (
                    Decimal(item.grams) * item.purchase_price_per_100g / Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Вычисляем прибыль
            profit = (sale_total - purchase_total).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Обновляем поля в позиции заказа
            item.sale_price_per_100g = sale_price_100g
            item.total_sale_price = sale_total
            item.profit = profit

            total_price += sale_total
            total_profit += profit

        # Обновляем поля в заказе
        order.total_price = total_price
        order.final_price = total_price
        order.profit = total_profit
        order.status = OrderStatus.DELIVERED.value

        await session.commit()
        await session.refresh(order)

        return order

    async def replace_status_on_return_transit(
            self,
            session: AsyncSession,
            order_id: int,
    ) -> Order:
        stmt = select(self.model).where(self.model.id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        order.status = OrderStatus.RETURN_TRANSIT.value

        await session.commit()
        await session.refresh(order)

        return order

    async def delete_order(self, session: AsyncSession, order):

        for item in order.items_rel:
            item.product.stock_grams += item.grams

        order.deleted_at = datetime.now()

        await session.commit()
        await session.refresh(order)

        return order

    async def soft_delete_order(self, session: AsyncSession, order: Order) -> Order:
        if order.deleted_at is not None:
            raise HTTPException(status_code=400, detail="Заказ уже удален")

        if order.status != OrderStatus.IN_TRANSIT.value:
            raise HTTPException(status_code=400, detail=f"Невозможно удалить заказ со статусом {order.status}")

        # Возвращаем сток
        for item in order.items_rel:
            product = item.product
            product.stock_grams += item.grams

        order.deleted_at = datetime.now()
        order.status = OrderStatus.DELETED.value

        await session.commit()
        await session.refresh(order)

        return order


    @staticmethod
    def _generate_order_number(user_name, delivery_service) -> str:
        return f"{user_name}-{delivery_service}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
