from datetime import datetime

from pydantic import BaseModel

from app.models.pipeline_run import PipelineStage, PipelineStatus
from app.models.validation import ValidationCategory


class PipelineRunResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    article_id: int
    current_stage: PipelineStage
    status: PipelineStatus
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str


class PipelineStartRequest(BaseModel):
    article_id: int
    auto_gate_one: bool = False
    format_id: str | None = None


class ValidationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    category: ValidationCategory
    item: str
    passed: bool
    score: float
    message: str


class ValidationSummary(BaseModel):
    total: int
    passed: int
    failed: int
    score: float
    by_category: dict[str, dict[str, int]]
