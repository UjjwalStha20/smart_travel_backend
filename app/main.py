from fastapi import FastAPI, Depends

from app.routers import accommodation, address, destination, food_cost
from .routers import user


app = FastAPI()

app.include_router(user.router)
app.include_router(destination.router)
app.include_router(address.router)
app.include_router(accommodation.router)
app.include_router(food_cost.router)



 



