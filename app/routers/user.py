from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import EmailStr
from sqlmodel import Session

from app.core.db import get_session
from app.dependencies import CurrentUser, SessionDep, require_admin
from app.models import User
from app.schemas import UserCreate, UserRead, UserUpdate
from app.schemas.pagination import PaginatedResponse
from app.services.user_service import UserService
from app.services.activity_log_service import ActivityLogService

router = APIRouter(prefix="/users", tags=["users"])

class UserRouter:

    @router.get("/", response_model=PaginatedResponse[UserRead], status_code=200)
    def get_users(session: Session = Depends(get_session), offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), email: Optional[EmailStr] = None):
        users = UserService(session).get_all_users(offset=offset, limit=limit, email=email)
        return users
    

    @router.get("/{user_id}")
    async def get_user_by_id(session: SessionDep, user_id: str) -> UserRead :
        """Get a user by ID."""
        # In a real application, you would fetch the user from the database 
        user = UserService(session).get_user_by_id(user_id)
        return user

    @router.post("/")
    async def create_user(session: SessionDep, user: UserCreate, admin: Annotated[User, Depends(require_admin)]):
        """Create a new user."""
        created = UserService(session).create_user(user)
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Created", target=f"User: {created.name}", type="user",
        )
        return {"message": "User created successfully", "user": created}
    
    @router.put("/{user_id}")
    async def update_user(session: SessionDep, user_id: str, user: UserUpdate, current_user: CurrentUser):
        """Update a user by ID."""
        if str(current_user.id) != user_id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not your profile")
        update_user = UserService(session).update_user(user_id, user)
        return {"message": "User updated successfully", "user": update_user}
    
    @router.delete("/{user_id}")
    async def delete_user(session: SessionDep, user_id: str, current_user: CurrentUser):
        """Delete a user by ID."""
        if str(current_user.id) != user_id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not your profile")
        target = UserService(session).get_user_by_id(user_id)
        user_deleted = UserService(session).delete_user(user_id)
        if user_deleted:
            ActivityLogService(session).log(
                user_id=current_user.id, user_name=current_user.name,
                action="Deleted", target=f"User: {target.name}", type="user",
            )
            return {"message": "User deleted successfully"}
        return {"message": "User not found"}