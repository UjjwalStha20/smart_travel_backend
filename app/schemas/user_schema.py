from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from app.models.user_model import UserRole


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    role: UserRole
    nationality: Optional[str] = Field(default=None, min_length=1)
    email: EmailStr
    phone: Optional[str] = Field(default=None, pattern=r'^\+?[0-9\-\s]+$')
    

class UserCreate(UserBase):
    password: str = Field(min_length=6)

class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class UserUpdate(UserBase):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, pattern=r'^\+?[0-9\-\s]+$')
