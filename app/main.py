from fastapi import FastAPI

from app.routers import (auth,
    accommodation,
    address,
    attraction,
    destination,
    entry_fee,
    food_cost,
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


app = FastAPI()

app.include_router(auth.router)
app.include_router(accommodation.router)
app.include_router(address.router)
app.include_router(attraction.router)
app.include_router(destination.router)
app.include_router(entry_fee.router)
app.include_router(food_cost.router)
app.include_router(itinerary.router)
app.include_router(permit.router)
app.include_router(photo.router)
app.include_router(review.router)
app.include_router(route_point.router)
app.include_router(saved_destination.router)
app.include_router(trekking_route.router)
app.include_router(user.router)
app.include_router(user_trip.router)



 



