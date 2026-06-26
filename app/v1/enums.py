from enum import Enum


class ProductStatusEnum(str, Enum):
    WAREHOUSE = "warehouse"
    TRANSIT = "transit"
    DELIVERED = "delivered"
    RETURN_TRANSIT = "return_transit"


class OrderStatus(str, Enum):
    IN_TRANSIT = "transit"
    DELIVERED = "delivered"
    RETURN_TRANSIT = "return_transit"
    RETURNED_ON_WAREHOUSE = "returned_on_warehouse"
    DELETED = "deleted"


# =====================================================
# ENUM ДЛЯ ТИПОВ ТРАНЗАКЦИЙ
# =====================================================
class TransactionType(Enum):
    """
    Типы транзакций кошелька
    """
    SALE = "sale"  # - продажа - при продаже товара +
    RETURN = "return"  # "return" - возврат - в случае возврата товара после продажи +
    PURCHASE = "purchase"  # "purchase" - вывод в случае новой закупки волос (Новая закупка)
    TRANSFER = "transfer"  # "transfer" - вывод - в случае каких-либо расходов (пакеты, резинки и т.д.) +
    DEPOSIT = "deposit"  # "deposit" - пополнение (приход) - в случае пополнения кошелька +
    WITHDRAWAL = "withdrawal"  # "withdrawal" - вывод (расход) - в случае вывода средств +
