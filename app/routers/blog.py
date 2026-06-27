from fastapi import APIRouter, Query

from app.dependencies import SessionDep
from app.models import Blog
from app.schemas import BlogCreate, BlogUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import BlogService

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
    async def create(data: BlogCreate, session: SessionDep):
        return BlogService(session).create(data)

    @router.put("/{blog_id}", response_model=Blog, status_code=200)
    async def update(blog_id: str, data: BlogUpdate, session: SessionDep):
        return BlogService(session).update(blog_id, data)

    @router.delete("/{blog_id}", status_code=200)
    async def delete(blog_id: str, session: SessionDep):
        return BlogService(session).delete(blog_id)
