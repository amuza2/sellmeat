from fastapi import FastAPI

from app.routers import (
    auth,
    meat_types,
    categories,
    products,
    delivery_slots,
    settings,
    orders,
)

app = FastAPI(title="SellMeat API", version="0.1.0")


@app.get("/")
def root():
    return {"name": "SellMeat API", "status": "running"}


app.include_router(auth.router)
app.include_router(meat_types.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(delivery_slots.router)
app.include_router(settings.router)
app.include_router(orders.router)
