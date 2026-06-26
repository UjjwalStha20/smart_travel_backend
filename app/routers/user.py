from typing import List

from fastapi import APIRouter
from fastapi.params import Depends
from pydantic import EmailStr
from sqlmodel import Session

from app.core.db import get_session
from app.dependencies import SessionDep
from app.schemas import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

class UserRouter:

    @router.get("/", response_model=list[UserRead] , status_code=200)
    def get_users(session: Session = Depends(get_session),email: EmailStr = None)-> List[UserRead]: 
        users = UserService(session).get_all_users(offset=0, limit=100, email=email)              
        return users
    

    @router.get("/{user_id}")
    async def get_user_by_id(session: SessionDep, user_id: str) -> UserRead :
        """Get a user by ID."""
        # In a real application, you would fetch the user from the database 
        user = UserService(session).get_user_by_id(user_id)
        return user

    @router.post("/")
    async def create_user(session: SessionDep, user: UserCreate):
        """Create a new user."""
        # In a real application, you would save the user to the database
        create_user = UserService(session).create_user(user)
        return {"message": "User created successfully", "user": create_user}
    
    @router.put("/{user_id}")
    async def update_user(session: SessionDep, user_id: str, user: UserUpdate):
        """Update a user by ID."""
        # In a real application, you would update the user in the database
        update_user = UserService(session).update_user(user_id, user)
        return {"message": "User updated successfully", "user": update_user}
    @router.delete("/{user_id}")
    async def delete_user(session: SessionDep, user_id: str):
        """Delete a user by ID."""
        # In a real application, you would delete the user from the database
        user_deleted = UserService(session).delete_user(user_id)
        if user_deleted:
            return {"message": "User deleted successfully"}
        return {"message": "User not found"}