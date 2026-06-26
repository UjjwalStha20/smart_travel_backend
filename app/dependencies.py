from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import Session

from app.core.auth import get_current_user
from app.core.db import get_session
from app.models import User

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user