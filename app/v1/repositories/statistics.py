from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional

from sqlalchemy import func, select, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models import WalletTransaction
from app.v1.enums import TransactionType
from app.v1.repositories.common import CommonRepository


class SalesRepository(CommonRepository):
    """
    Репозиторий для работы с продажами и транзакциями.

    Наследуется от CommonRepository, модель — WalletTransaction.
    Предоставляет методы для получения статистики по продажам,
    расходам (TRANSFER) и чистой прибыли.

    Основные типы транзакций:
    - SALE — продажа (прибыль)
    - TRANSFER — расходы (пакеты, резинки и т.д.)
    - DEPOSIT — пополнение
    - WITHDRAWAL — вывод
    - RETURN — возврат
    - PURCHASE — закупка
    """
    model = WalletTransaction

    # ============================================
    # МЕТОД №1: ОБЩАЯ СТАТИСТИКА ПО ПРОДАЖАМ
    # ============================================

    async def get_sales_stats(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Возвращает общую статистику по продажам с учётом расходов (TRANSFER).
        """
        # Сумма продаж — ТОЛЬКО sale_amount, ТОЛЬКО для SALE
        stmt_sales = select(
            func.coalesce(func.sum(self.model.sale_amount), 0).label("total_sales")  # 👈 ИСПРАВЛЕНО
        ).where(func.lower(self.model.transaction_type) == "sale")

        result_sales = await session.execute(stmt_sales)
        total_sales = result_sales.scalar() or Decimal(0)

        # Количество продаж
        stmt_count = select(
            func.count().label("count")
        ).where(func.lower(self.model.transaction_type) == "sale")

        result_count = await session.execute(stmt_count)
        sales_count = result_count.scalar() or 0

        # Общая прибыль
        stmt_profit = select(
            func.coalesce(func.sum(self.model.profit_amount), 0).label("total_profit")
        ).where(func.lower(self.model.transaction_type) == "sale")

        result_profit = await session.execute(stmt_profit)
        total_profit = result_profit.scalar() or Decimal(0)

        # Общие расходы (TRANSFER) — ТОЛЬКО amount
        stmt_transfer = select(
            func.coalesce(func.sum(self.model.amount), 0).label("total_transfer")  # 👈 ИСПРАВЛЕНО
        ).where(self.model.transaction_type == TransactionType.TRANSFER.value)

        result_transfer = await session.execute(stmt_transfer)
        total_transfer = result_transfer.scalar() or Decimal(0)

        # Чистая прибыль
        net_profit = total_profit - total_transfer

        # Дополнительные показатели
        avg_check = total_sales / sales_count if sales_count > 0 else Decimal(0)
        profitability = (net_profit / total_sales * 100) if total_sales > 0 else Decimal(0)
        avg_profit = total_profit / sales_count if sales_count > 0 else Decimal(0)

        max_sale = await session.scalar(
            select(func.max(self.model.sale_amount))
            .where(func.lower(self.model.transaction_type) == "sale")
        ) or Decimal(0)

        min_sale = await session.scalar(
            select(func.min(self.model.sale_amount))
            .where(func.lower(self.model.transaction_type) == "sale")
        ) or Decimal(0)

        expense_ratio = (total_transfer / total_profit * 100) if total_profit > 0 else Decimal(0)

        return {
            "total_sales": total_sales,
            "sales_count": sales_count,
            "total_profit": total_profit,
            "total_transfer": total_transfer,
            "net_profit": net_profit,
            "avg_check": avg_check,
            "profitability": profitability,
            "avg_profit": avg_profit,
            "max_sale": max_sale,
            "min_sale": min_sale,
            "expense_ratio": expense_ratio,
        }

    # ============================================
    # МЕТОД №2: ПРОДАЖИ ПО МЕСЯЦАМ (С УЧЁТОМ TRANSFER)
    # ============================================

    async def get_sales_by_month(
            self,
            session: AsyncSession,
            year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Возвращает продажи и расходы по месяцам за указанный год.
        """
        if year is None:
            year = func.extract('year', func.now())

        # 1. Продажи по месяцам — ТОЛЬКО sale_amount
        stmt_sales = select(
            extract('month', self.model.created_at).label("month"),
            func.coalesce(func.sum(self.model.sale_amount), 0).label("total_sales"),  # 👈 ИСПРАВЛЕНО
            func.coalesce(func.sum(self.model.profit_amount), 0).label("total_profit"),
            func.count().label("sales_count")
        ).where(
            func.lower(self.model.transaction_type) == "sale",
            extract('year', self.model.created_at) == year
        ).group_by(extract('month', self.model.created_at))

        result_sales = await session.execute(stmt_sales)
        sales_by_month = result_sales.all()

        # 2. Расходы по месяцам (TRANSFER) — ТОЛЬКО amount
        stmt_transfer = select(
            extract('month', self.model.created_at).label("month"),
            func.coalesce(func.sum(self.model.amount), 0).label("total_transfer")  # 👈 ИСПРАВЛЕНО
        ).where(
            self.model.transaction_type == TransactionType.TRANSFER.value,
            extract('year', self.model.created_at) == year
        ).group_by(extract('month', self.model.created_at))

        result_transfer = await session.execute(stmt_transfer)
        transfer_by_month = {row.month: row.total_transfer for row in result_transfer.all()}

        # 3. Объединяем результаты
        result = []
        for row in sales_by_month:
            month = int(row.month)
            transfer = transfer_by_month.get(month, Decimal(0))

            result.append({
                "month": month,
                "month_name": self._get_month_name(month),
                "total_sales": row.total_sales or Decimal(0),
                "total_profit": row.total_profit or Decimal(0),
                "sales_count": row.sales_count or 0,
                "total_transfer": transfer,
                "net_profit": (row.total_profit or Decimal(0)) - transfer,
            })

        # 4. Добавляем месяцы без продаж (только расходы)
        for month, transfer in transfer_by_month.items():
            if not any(r["month"] == month for r in result):
                result.append({
                    "month": month,
                    "month_name": self._get_month_name(month),
                    "total_sales": Decimal(0),
                    "total_profit": Decimal(0),
                    "sales_count": 0,
                    "total_transfer": transfer,
                    "net_profit": -transfer,
                })

        # 5. Сортируем по месяцам
        result.sort(key=lambda x: x["month"])
        return result

    # ============================================
    # МЕТОД №3: ПРОДАЖИ ЗА ПОСЛЕДНИЕ N МЕСЯЦЕВ
    # ============================================

    async def get_recent_sales(
            self,
            session: AsyncSession,
            months: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Возвращает продажи за последние N месяцев.
        Использует ТУ ЖЕ логику, что и get_all_years_monthly_stats.
        """
        from dateutil.relativedelta import relativedelta

        now = datetime.now()
        start_date = now - relativedelta(months=months)

        stmt = select(
            extract('year', self.model.created_at).label("year"),
            extract('month', self.model.created_at).label("month"),
            func.coalesce(func.sum(self.model.sale_amount), 0).label("total_sales"),
            func.coalesce(func.sum(self.model.profit_amount), 0).label("total_profit"),
            func.count().label("sales_count")
        ).where(
            func.lower(self.model.transaction_type) == "sale",
            self.model.created_at >= start_date
        ).group_by(
            extract('year', self.model.created_at),
            extract('month', self.model.created_at)
        ).order_by(
            extract('year', self.model.created_at).desc(),
            extract('month', self.model.created_at).desc()
        )

        result = await session.execute(stmt)
        rows = result.all()

        # Строим словарь с данными
        data_by_month = {}
        for row in rows:
            key = f"{int(row.year)}-{int(row.month):02d}"
            data_by_month[key] = {
                "year": int(row.year),
                "month": int(row.month),
                "month_name": self._get_month_name(int(row.month)),
                "total_sales": row.total_sales or Decimal(0),
                "total_profit": row.total_profit or Decimal(0),
                "sales_count": row.sales_count or 0,
            }

        # Формируем последние N месяцев (включая пустые)
        result = []
        for i in range(months - 1, -1, -1):
            date = now - relativedelta(months=i)
            key = f"{date.year}-{date.month:02d}"
            if key in data_by_month:
                result.append(data_by_month[key])
            else:
                result.append({
                    "year": date.year,
                    "month": date.month,
                    "month_name": self._get_month_name(date.month),
                    "total_sales": Decimal(0),
                    "total_profit": Decimal(0),
                    "sales_count": 0,
                })

        return result

    # ============================================
    # МЕТОД №4: ДЕТАЛЬНЫЙ ОТЧЁТ ПО ПРОДАЖАМ
    # ============================================

    async def get_detailed_sales_report(
            self,
            session: AsyncSession,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Возвращает детальный отчёт по продажам с фильтром по датам.
        """
        conditions = [func.lower(self.model.transaction_type) == "sale"]

        if start_date:
            conditions.append(self.model.created_at >= start_date)
        if end_date:
            conditions.append(self.model.created_at <= end_date)

        stmt_stats = select(
            func.coalesce(func.sum(self.model.sale_amount), 0).label("total_sales"),  # 👈 ИСПРАВЛЕНО
            func.coalesce(func.sum(self.model.profit_amount), 0).label("total_profit"),
            func.count().label("sales_count"),
            func.coalesce(func.avg(self.model.sale_amount), 0).label("avg_sale")
        ).where(*conditions)

        result_stats = await session.execute(stmt_stats)
        stats = result_stats.one()

        stmt_transactions = select(self.model).where(*conditions).order_by(
            self.model.created_at.desc()
        )
        result_transactions = await session.execute(stmt_transactions)
        transactions = result_transactions.scalars().all()

        return {
            "total_sales": stats.total_sales or Decimal(0),
            "total_profit": stats.total_profit or Decimal(0),
            "sales_count": stats.sales_count or 0,
            "avg_sale": stats.avg_sale or Decimal(0),
            "transactions": transactions,
            "period": {
                "start": start_date,
                "end": end_date,
            }
        }

    # ============================================
    # МЕТОД №5: СТАТИСТИКА ПО МЕСЯЦАМ ЗА ВСЕ ГОДА
    # ============================================

    async def get_all_years_monthly_stats(
            self,
            session: AsyncSession
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Возвращает статистику по месяцам для каждого года (все годы).
        """
        # Продажи по месяцам и годам
        stmt_sales = select(
            extract('year', self.model.created_at).label("year"),
            extract('month', self.model.created_at).label("month"),
            func.coalesce(func.sum(self.model.sale_amount), 0).label("total_sales"),  # 👈 ИСПРАВЛЕНО
            func.coalesce(func.sum(self.model.profit_amount), 0).label("total_profit"),
            func.count().label("sales_count")
        ).where(
            func.lower(self.model.transaction_type) == "sale"
        ).group_by(
            extract('year', self.model.created_at),
            extract('month', self.model.created_at)
        ).order_by(
            extract('year', self.model.created_at).desc(),
            extract('month', self.model.created_at)
        )

        result_sales = await session.execute(stmt_sales)
        sales_data = result_sales.all()

        # Расходы по месяцам и годам (TRANSFER) — ТОЛЬКО amount
        stmt_transfer = select(
            extract('year', self.model.created_at).label("year"),
            extract('month', self.model.created_at).label("month"),
            func.coalesce(func.sum(self.model.amount), 0).label("total_transfer")  # 👈 ИСПРАВЛЕНО
        ).where(
            self.model.transaction_type == TransactionType.TRANSFER.value
        ).group_by(
            extract('year', self.model.created_at),
            extract('month', self.model.created_at)
        )

        result_transfer = await session.execute(stmt_transfer)
        transfer_data = result_transfer.all()

        transfer_by_year = {}
        for row in transfer_data:
            year = int(row.year)
            month = int(row.month)
            if year not in transfer_by_year:
                transfer_by_year[year] = {}
            transfer_by_year[year][month] = row.total_transfer or Decimal(0)

        result = {}
        for row in sales_data:
            year = int(row.year)
            month = int(row.month)

            if year not in result:
                result[year] = []

            transfer = transfer_by_year.get(year, {}).get(month, Decimal(0))

            result[year].append({
                "month": month,
                "month_name": self._get_month_name(month),
                "total_sales": row.total_sales or Decimal(0),
                "total_profit": row.total_profit or Decimal(0),
                "sales_count": row.sales_count or 0,
                "total_transfer": transfer,
                "net_profit": (row.total_profit or Decimal(0)) - transfer,
            })

        for year, months in transfer_by_year.items():
            if year not in result:
                result[year] = []
            for month, transfer in months.items():
                if not any(m["month"] == month for m in result.get(year, [])):
                    result[year].append({
                        "month": month,
                        "month_name": self._get_month_name(month),
                        "total_sales": Decimal(0),
                        "total_profit": Decimal(0),
                        "sales_count": 0,
                        "total_transfer": transfer,
                        "net_profit": -transfer,
                    })

        for year in result:
            result[year].sort(key=lambda x: x["month"])

        return result

    # ============================================
    # МЕТОД №6: ГОДОВАЯ СВОДКА ПО ВСЕМ ГОДАМ
    # ============================================

    async def get_yearly_summary(
            self,
            session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Возвращает сводку по годам: общая прибыль, расходы, продажи.
        """
        # Продажи по годам
        stmt_sales = select(
            extract('year', self.model.created_at).label("year"),
            func.coalesce(func.sum(self.model.sale_amount), 0).label("total_sales"),  # 👈 ИСПРАВЛЕНО
            func.coalesce(func.sum(self.model.profit_amount), 0).label("total_profit"),
            func.count().label("sales_count")
        ).where(
            func.lower(self.model.transaction_type) == "sale"
        ).group_by(extract('year', self.model.created_at))

        result_sales = await session.execute(stmt_sales)
        sales_data = {int(row.year): row for row in result_sales.all()}

        # Расходы по годам (TRANSFER) — ТОЛЬКО amount
        stmt_transfer = select(
            extract('year', self.model.created_at).label("year"),
            func.coalesce(func.sum(self.model.amount), 0).label("total_transfer")  # 👈 ИСПРАВЛЕНО
        ).where(
            self.model.transaction_type == TransactionType.TRANSFER.value
        ).group_by(extract('year', self.model.created_at))

        result_transfer = await session.execute(stmt_transfer)
        transfer_data = {int(row.year): row.total_transfer for row in result_transfer.all()}

        all_years = set(sales_data.keys()) | set(transfer_data.keys())

        result = []
        for year in sorted(all_years, reverse=True):
            sales = sales_data.get(year)
            transfer = transfer_data.get(year, Decimal(0))

            total_sales = sales.total_sales if sales else Decimal(0)
            total_profit = sales.total_profit if sales else Decimal(0)
            sales_count = sales.sales_count if sales else 0
            net_profit = total_profit - transfer

            result.append({
                "year": year,
                "total_sales": total_sales,
                "total_profit": total_profit,
                "sales_count": sales_count,
                "total_transfer": transfer,
                "net_profit": net_profit,
            })

        return result

    # ============================================
    # МЕТОД №7: ДАННЫЕ ДЛЯ ГРАФИКА
    # ============================================

    async def get_monthly_chart_data(
            self,
            session: AsyncSession,
            year: Optional[int] = None
    ) -> Dict[str, List]:
        """
        Возвращает данные для построения графика.
        """
        data = await self.get_sales_by_month_full(session, year)

        return {
            "months": [d["month_name"] for d in data],
            "profit": [float(d["net_profit"]) for d in data],
            "sales": [float(d["total_sales"]) for d in data],
            "transfer": [float(d["total_transfer"]) for d in data],
        }

    # ============================================
    # ВСПОМОГАТЕЛЬНЫЙ МЕТОД
    # ============================================

    def _get_month_name(self, month: int) -> str:
        months = {
            1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
            5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
            9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
        }
        return months.get(month, str(month))

    # ============================================
    # МЕТОД №8: ПОЛНЫЙ СПИСОК МЕСЯЦЕВ (ДАЖЕ ПУСТЫХ)
    # ============================================

    def _get_all_months(self) -> List[Dict[str, Any]]:
        months = []
        for i in range(1, 13):
            months.append({
                "month": i,
                "month_name": self._get_month_name(i),
                "total_sales": Decimal(0),
                "total_profit": Decimal(0),
                "sales_count": 0,
                "total_transfer": Decimal(0),
                "net_profit": Decimal(0),
            })
        return months

    async def get_sales_by_month_full(
            self,
            session: AsyncSession,
            year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Возвращает данные по месяцам за указанный год.
        Возвращает ВСЕ 12 месяцев, даже если в них не было продаж.
        """
        data = await self.get_sales_by_month(session, year)
        data_by_month = {item["month"]: item for item in data}

        result = []
        for i in range(1, 13):
            if i in data_by_month:
                result.append(data_by_month[i])
            else:
                result.append({
                    "month": i,
                    "month_name": self._get_month_name(i),
                    "total_sales": Decimal(0),
                    "total_profit": Decimal(0),
                    "sales_count": 0,
                    "total_transfer": Decimal(0),
                    "net_profit": Decimal(0),
                })

        return result

    # ============================================
    # МЕТОД №9: ТОП-ТОВАРЫ (ЕСЛИ ЕСТЬ СВЯЗЬ)
    # ============================================

    async def get_top_products(
            self,
            session: AsyncSession,
            limit: int = 10,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Возвращает топ-N товаров по продажам."""
        # TODO: Реализовать когда появится связь с товарами
        return []

    # ============================================
    # МЕТОД №10: ДИНАМИКА ПО ДНЯМ
    # ============================================

    async def get_daily_sales(
            self,
            session: AsyncSession,
            days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Возвращает продажи по дням за последние N дней.
        """
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)

        stmt = select(
            func.date(self.model.created_at).label("date"),
            func.coalesce(func.sum(self.model.sale_amount), 0).label("total_sales"),  # 👈 ИСПРАВЛЕНО
            func.coalesce(func.sum(self.model.profit_amount), 0).label("total_profit"),
            func.count().label("sales_count")
        ).where(
            func.lower(self.model.transaction_type) == "sale",
            self.model.created_at >= start_date
        ).group_by(
            func.date(self.model.created_at)
        ).order_by(
            func.date(self.model.created_at)
        )

        result = await session.execute(stmt)
        rows = result.all()

        return [
            {
                "date": row.date.strftime("%Y-%m-%d"),
                "total_sales": row.total_sales or Decimal(0),
                "total_profit": row.total_profit or Decimal(0),
                "sales_count": row.sales_count or 0,
            }
            for row in rows
        ]