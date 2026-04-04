from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.v1.routers import products
from app.v1.routers import orders
from app.v1.routers import index

app_v1 = FastAPI(title="CRM hair API v1", version="1.0.0")

app_v1.include_router(products.router, prefix="/hairs", tags=["hairs"])
#app_v1.include_router(orders.router, prefix="/orders", tags=["orders"])
app_v1.include_router(index.router, prefix="/index", tags=["index"])

app_v1.mount("/static", StaticFiles(directory="app/v1/static"), name="static")
templates = Jinja2Templates(directory="app/v1/templates")
