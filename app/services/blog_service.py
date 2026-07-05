from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import Blog


class BlogService:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self, offset: int = 0, limit: int = 100):
        statement = select(Blog).offset(offset).limit(limit)
        items = self.session.exec(statement).all()
        total = self.session.exec(select(func.count(Blog.id))).one()
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    def get_by_id(self, blog_id: UUID) -> Blog:
        blog = self.session.get(Blog, blog_id)
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        return blog

    def get_by_slug(self, slug: str) -> Blog:
        blog = self.session.exec(select(Blog).where(Blog.slug == slug)).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        return blog

    def get_by_category(self, category: str):
        statement = select(Blog).where(Blog.category == category).order_by(Blog.created_at.desc())
        return self.session.exec(statement).all()

    def create(self, data: Blog) -> Blog:
        blog = Blog(**data.model_dump())
        self.session.add(blog)
        self.session.commit()
        self.session.refresh(blog)
        return blog

    def update(self, blog_id: UUID, data: Blog) -> Blog:
        existing = self.get_by_id(blog_id)
        patch = data.model_dump(exclude_unset=True)
        existing.sqlmodel_update(patch)
        existing.updated_at = func.now()
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def delete(self, blog_id: UUID) -> dict:
        blog = self.get_by_id(blog_id)
        self.session.delete(blog)
        self.session.commit()
        return {"message": "Blog deleted successfully"}
