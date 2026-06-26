from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import HTTPException
from pydantic import EmailStr
from sqlmodel import Session, func, select

from app.core.security import hash_password
from app.models import User


class UserService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_users(self, offset: int = 0, limit: int = 100, email: EmailStr = None) -> List[User]:
        statement = select(User).offset(offset).limit(limit)
        if email:
            statement = statement.where(User.email == email)
        items = self.session.exec(statement).all()
        total = self.session.exec(select(func.count(User.id))).one()
        return {"items": items, "total": total, "offset": offset, "limit": limit}
    
    def get_user_by_id(self, user_id: UUID) -> User:
        user = self.session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def get_user_by_email(self, email: EmailStr) -> User | None:
        return self.session.exec(
            select(User).where(User.email == email)
        ).first()

    def create_user(self, user_data: User)-> User:
        existing = self.get_user_by_email(user_data.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already exists")
        user_data.password = hash_password(user_data.password)
        user = User(**user_data.model_dump())
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_user(self, user_id: UUID, user_data: User) -> User:
        existing_user = self.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        check_email = self.session.exec(
            select(User).where(User.email == user_data.email, User.id != user_id)
        ).first()
        if check_email:
            raise HTTPException(status_code=409, detail="Email already exists")
        existing_user.updated_at = datetime.now(timezone.utc)
        patch = user_data.model_dump(exclude_unset=True)
        existing_user.sqlmodel_update(patch)
        self.session.add(existing_user)
        self.session.commit()
        self.session.refresh(existing_user)
        print(existing_user)
        return existing_user

    def delete_user(self, user_id: UUID) -> None:
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        self.session.delete(user)
        self.session.commit()
        