import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

from app.core.rate_limit import limiter

from app.core.logging import setup_logging
from app.routers import (auth,
    accommodation,
    address,
    attraction,
    chat,
    destination,
    entry_fee,
    food_cost,
    health,
    itinerary,
    permit,
    photo,
    review,
    route_point,
    saved_destination,
    trekking_route,
    user,
    user_trip,
)

setup_logging()

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(accommodation.router)
app.include_router(address.router)
app.include_router(attraction.router)
app.include_router(chat.router)
app.include_router(destination.router)
app.include_router(entry_fee.router)
app.include_router(food_cost.router)
app.include_router(itinerary.router)
app.include_router(permit.router)
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(photo.router)
app.include_router(review.router)
app.include_router(route_point.router)
app.include_router(saved_destination.router)
app.include_router(trekking_route.router)
app.include_router(user.router)
app.include_router(user_trip.router)



 



