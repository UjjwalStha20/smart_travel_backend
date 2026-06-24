from fastapi import FastAPI, Depends

from app.routers import accommodation, address, destination, food_cost
from .routers import user
from contextlib import asynccontextmanager
from .core.db import engine, init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to database...")
    engine
    init_db()
    engine.connect()
    yield
    # Perform any shutdown tasks here (e.g., disconnect from the database)
    print("Disconnecting from database...")

app = FastAPI(lifespan=lifespan)
app.include_router(user.router)
app.include_router(destination.router)
app.include_router(address.router)
app.include_router(accommodation.router)
app.include_router(food_cost.router)



 



