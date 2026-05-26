from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.article import Article
    from app.models.validation import Validation


class PipelineStage(enum.StrEnum):
    ROUTER = "router"
    RESEARCHER = "researcher"
    OUTLINER = "outliner"
    GATE_ONE = "gate_one"
    GENERATOR = "generator"
    VALIDATOR = "validator"
    GATE_TWO = "gate_two"
    PUBLISHER = "publisher"


class PipelineStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineRun(TimestampMixin, Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))
    current_stage: Mapped[PipelineStage] = mapped_column(
        Enum(PipelineStage), default=PipelineStage.ROUTER
    )
    status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus), default=PipelineStatus.PENDING
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    retry_count: Mapped[int] = mapped_column(default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    stage_durations: Mapped[dict] = mapped_column(JSON, default=dict)

    article: Mapped[Article] = relationship(back_populates="pipeline_runs")
    validations: Mapped[list[Validation]] = relationship(
        back_populates="pipeline_run",
        cascade="all, delete-orphan",
    )
