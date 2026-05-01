from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.v1.middlewares.auth_middleware import AuthMiddleware
from app.v1.routers import products
from app.v1.routers import orders
from app.v1.routers import index
from app.v1.routers import auth_pages
from app.v1.routers import site_pages


app_v1 = FastAPI(title="CRM hair API v1", version="1.0.0")

app_v1.mount("/static", StaticFiles(directory="app/v1/static"), name="static")

app_v1.add_middleware(AuthMiddleware)

app_v1.include_router(auth_pages.router, prefix="/auth_pages", tags=["auth_pages"])
app_v1.include_router(site_pages.router, prefix="/site_pages", tags=["site_pages"])
app_v1.include_router(products.router, prefix="/hairs", tags=["hairs"])
app_v1.include_router(orders.router, prefix="/orders", tags=["orders"])
app_v1.include_router(index.router, prefix="/index", tags=["index"])
