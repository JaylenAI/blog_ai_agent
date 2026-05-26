from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import get_article_service
from app.schemas.common import ApiResponse
from app.services.article_service import ArticleService

router = APIRouter()


class ScheduleRequest(BaseModel):
    scheduled_at: datetime


class CalendarEntry(BaseModel):
    article_id: int
    title: str
    topic: str
    status: str
    scheduled_at: datetime | None
    published_at: datetime | None


@router.get("")
async def get_calendar(
    service: ArticleService = Depends(get_article_service),
) -> ApiResponse[list[CalendarEntry]]:
    articles, _total = await service.list_all(limit=100, offset=0)
    entries = [
        CalendarEntry(
            article_id=a.id,
            title=a.title,
            topic=a.topic,
            status=a.status.value,
            scheduled_at=a.scheduled_at,
            published_at=a.published_at,
        )
        for a in articles
    ]
    return ApiResponse(success=True, data=entries)


@router.put("/{article_id}/schedule")
async def schedule_article(
    article_id: int,
    data: ScheduleRequest,
    service: ArticleService = Depends(get_article_service),
) -> ApiResponse[CalendarEntry]:
    article = await service.get_by_id(article_id)
    if not article:
        return ApiResponse(success=False, error="아티클을 찾을 수 없습니다")

    article.scheduled_at = data.scheduled_at
    await service._repo._session.flush()
    await service._repo._session.commit()

    return ApiResponse(
        success=True,
        data=CalendarEntry(
            article_id=article.id,
            title=article.title,
            topic=article.topic,
            status=article.status.value,
            scheduled_at=article.scheduled_at,
            published_at=article.published_at,
        ),
    )


@router.delete("/{article_id}/schedule")
async def unschedule_article(
    article_id: int,
    service: ArticleService = Depends(get_article_service),
) -> ApiResponse[dict]:
    article = await service.get_by_id(article_id)
    if not article:
        return ApiResponse(success=False, error="아티클을 찾을 수 없습니다")

    article.scheduled_at = None
    await service._repo._session.flush()
    await service._repo._session.commit()

    return ApiResponse(success=True, data={"article_id": article_id, "scheduled_at": None})
