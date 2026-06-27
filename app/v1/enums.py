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
    SALE = "sale"  # - продажа - при продаже товара
    DEPOSIT = "deposit"  # "deposit" - пополнение (приход) - в случае пополнения кошелька
    WITHDRAWAL = "withdrawal"  # "withdrawal" - вывод - в случае вывода средств
    RETURN = "return"  # "return" - возврат - в случае возврата товара после продажи
    PURCHASE = "purchase"  # "purchase" - вывод в случае новой закупки волос (Новая закупка)
    TRANSFER = "transfer"  # "transfer" - расход - в случае каких-либо расходов (пакеты, резинки и т.д.)


