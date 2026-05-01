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
