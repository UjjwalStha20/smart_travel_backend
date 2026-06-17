from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr
from app.models.user_model import UserRole


class UserBase(BaseModel):
    name: str
    role: UserRole
    nationality: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class UserUpdate(UserBase):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
