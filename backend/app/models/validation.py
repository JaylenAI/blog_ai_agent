from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.pipeline_run import PipelineRun


class ValidationCategory(enum.StrEnum):
    STYLE = "style"
    SEO = "seo"
    AEO = "aeo"
    GEO = "geo"


class Validation(TimestampMixin, Base):
    __tablename__ = "validations"

    id: Mapped[int] = mapped_column(primary_key=True)
    pipeline_run_id: Mapped[int] = mapped_column(ForeignKey("pipeline_runs.id"))
    category: Mapped[ValidationCategory] = mapped_column(Enum(ValidationCategory))
    item: Mapped[str] = mapped_column(String(200))
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    message: Mapped[str] = mapped_column(Text, default="")

    pipeline_run: Mapped[PipelineRun] = relationship(back_populates="validations")
