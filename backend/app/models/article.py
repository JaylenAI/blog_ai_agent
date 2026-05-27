from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.pipeline_run import PipelineRun


class ArticleStatus(enum.StrEnum):
    DRAFT = "draft"
    RESEARCHING = "researching"
    OUTLINING = "outlining"
    GATE_ONE = "gate_one"
    GENERATING = "generating"
    VALIDATING = "validating"
    REVIEW = "review"
    PUBLISHED = "published"
    FAILED = "failed"


class Article(TimestampMixin, Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    topic: Mapped[str] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus), default=ArticleStatus.DRAFT
    )
    format_id: Mapped[str] = mapped_column(String(50), default="concept")
    content_path: Mapped[str] = mapped_column(String(500), default="")
    word_count: Mapped[int] = mapped_column(default=0)
    image_count: Mapped[int] = mapped_column(default=0)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    reference_count: Mapped[int] = mapped_column(default=0)
    section_count: Mapped[int] = mapped_column(default=0)
    thumbnail_path: Mapped[str] = mapped_column(String(500), default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_url: Mapped[str] = mapped_column(String(500), default="")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    extra_meta: Mapped[dict] = mapped_column(JSON, default=dict)

    pipeline_runs: Mapped[list[PipelineRun]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
    )
