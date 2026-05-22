from fastapi import APIRouter, HTTPException

from app.formats import get_format_registry
from app.formats.schema import FormatSuggestion, FormatSummary
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("")
async def list_formats() -> ApiResponse[list[FormatSummary]]:
    registry = get_format_registry()
    return ApiResponse(success=True, data=registry.list_summaries())


@router.get("/suggest")
async def suggest_format(topic: str) -> ApiResponse[list[FormatSuggestion]]:
    registry = get_format_registry()
    suggestions = registry.suggest(topic)
    return ApiResponse(success=True, data=suggestions)


@router.get("/{format_id}")
async def get_format(format_id: str) -> ApiResponse[dict]:
    registry = get_format_registry()
    if format_id not in registry.format_ids:
        raise HTTPException(status_code=404, detail=f"형식 '{format_id}'를 찾을 수 없습니다")
    spec = registry.get(format_id)
    return ApiResponse(success=True, data=spec.model_dump())
