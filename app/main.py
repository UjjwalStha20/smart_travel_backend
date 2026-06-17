from fastapi import FastAPI, Depends

from app.routers import destination
from .routers import user
from contextlib import asynccontextmanager
from .core.db import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to database...")
    engine
    engine.connect()
    yield
    # Perform any shutdown tasks here (e.g., disconnect from the database)
    print("Disconnecting from database...")

app = FastAPI(lifespan=lifespan)
app.include_router(user.router)
app.include_router(destination.router)


 



