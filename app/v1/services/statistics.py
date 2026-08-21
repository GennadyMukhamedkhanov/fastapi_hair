from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.v1.repositories.statistics import SalesRepository
from datetime import datetime


async def get_all_sales_services(
        session: AsyncSession,
        sales_repo: SalesRepository,
        year: Optional[int] = None,
        months: int = 6,
) -> Dict[str, Any]:
    """
    Сервис для получения полной статистики по продажам.
    """

    # 1. Общая статистика
    stats = await sales_repo.get_sales_stats(session)

    # 2. Продажи по месяцам за указанный год (ВСЕ 12 МЕСЯЦЕВ)
    monthly = await sales_repo.get_sales_by_month_full(session, year)

    # 3. Продажи за последние N месяцев
    recent = await sales_repo.get_recent_sales(session, months)

    # 4. Статистика по месяцам за все годы
    all_years = await sales_repo.get_all_years_monthly_stats(session)

    # 5. Сводка по годам
    yearly_summary = await sales_repo.get_yearly_summary(session)

    # 6. Данные для графика (текущий год)
    chart_data = await sales_repo.get_monthly_chart_data(session, year)

    # 7. Общая статистика по годам (для таблицы)
    total_by_year = {}
    for item in yearly_summary:
        total_by_year[item["year"]] = {
            "total_sales": item["total_sales"],
            "total_profit": item["total_profit"],
            "total_transfer": item["total_transfer"],
            "net_profit": item["net_profit"],
            "sales_count": item["sales_count"],
        }

    # 8. Список доступных годов для фильтрации
    available_years = sorted(
        [item["year"] for item in yearly_summary],
        reverse=True
    )

    # 9. Текущий выбранный год
    current_year = year or datetime.now().year

    return {
        "stats": stats,
        "monthly": monthly,
        "recent": recent,
        "all_years": all_years,
        "yearly_summary": yearly_summary,
        "total_by_year": total_by_year,
        "chart_data": chart_data,
        "available_years": available_years,
        "current_year": current_year,
        "months_count": months,
    }


def get_sales_repository() -> SalesRepository:
    return SalesRepository()