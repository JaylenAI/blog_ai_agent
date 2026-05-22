from datetime import datetime

from pydantic import BaseModel, Field

from app.models.article import ArticleStatus


class ArticleCreate(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500)
    title: str = Field(default="", max_length=200)
    category: str = Field(default="", max_length=100)
    format_id: str = Field(default="concept", max_length=50)


class ArticleUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    category: str | None = Field(default=None, max_length=100)
    status: ArticleStatus | None = None
    word_count: int | None = None


class ArticleResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    slug: str
    title: str
    topic: str
    category: str
    format_id: str
    status: ArticleStatus
    content_path: str
    word_count: int
    image_count: int
    created_at: datetime
    updated_at: datetime


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    page: int
    limit: int
