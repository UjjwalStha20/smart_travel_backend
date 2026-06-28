from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import SessionDep, require_admin
from app.models import Blog, User
from app.schemas import BlogCreate, BlogUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import BlogService
from app.services.activity_log_service import ActivityLogService

router = APIRouter(prefix="/blogs", tags=["Blogs"])


class BlogRouter:

    @router.get("/", response_model=PaginatedResponse[Blog], status_code=200)
    async def get_all(session: SessionDep, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
        return BlogService(session).get_all(offset=offset, limit=limit)

    @router.get("/by-category/{category}", response_model=list[Blog], status_code=200)
    async def get_by_category(category: str, session: SessionDep):
        return BlogService(session).get_by_category(category)

    @router.get("/by-slug/{slug}", response_model=Blog, status_code=200)
    async def get_by_slug(slug: str, session: SessionDep):
        return BlogService(session).get_by_slug(slug)

    @router.get("/{blog_id}", response_model=Blog, status_code=200)
    async def get_by_id(blog_id: str, session: SessionDep):
        return BlogService(session).get_by_id(blog_id)

    @router.post("/", response_model=Blog, status_code=201)
    async def create(data: BlogCreate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        result = BlogService(session).create(data)
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Created", target=f"Blog: {result.title}", type="content",
        )
        return result

    @router.put("/{blog_id}", response_model=Blog, status_code=200)
    async def update(blog_id: str, data: BlogUpdate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        result = BlogService(session).update(blog_id, data)
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Updated", target=f"Blog: {result.title}", type="content",
        )
        return result

    @router.delete("/{blog_id}", status_code=200)
    async def delete(blog_id: str, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        blog = BlogService(session).get_by_id(blog_id)
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Deleted", target=f"Blog: {blog.title}", type="content",
        )
        return BlogService(session).delete(blog_id)
