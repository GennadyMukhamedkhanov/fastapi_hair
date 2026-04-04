#from app.v1.repositories.orders import OrderRepository
from app.v1.repositories.products import ProductRepository


async def get_product_repository() -> ProductRepository:
    return ProductRepository()
#
# async def get_order_repository() -> OrderRepository:
#     return OrderRepository()
