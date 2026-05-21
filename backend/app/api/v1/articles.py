from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_article_service
from app.schemas.article import (
    ArticleCreate,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
)
from app.schemas.common import ApiResponse
from app.services.article_service import ArticleService

router = APIRouter()


@router.post("")
async def create_article(
    data: ArticleCreate,
    service: ArticleService = Depends(get_article_service),
) -> ApiResponse[ArticleResponse]:
    article = await service.create(data)
    return ApiResponse(
        success=True,
        data=ArticleResponse.model_validate(article),
    )


@router.get("")
async def list_articles(
    page: int = 1,
    limit: int = 20,
    service: ArticleService = Depends(get_article_service),
) -> ApiResponse[ArticleListResponse]:
    offset = (page - 1) * limit
    articles, total = await service.list_all(offset=offset, limit=limit)
    return ApiResponse(
        success=True,
        data=ArticleListResponse(
            items=[ArticleResponse.model_validate(a) for a in articles],
            total=total,
            page=page,
            limit=limit,
        ),
    )


@router.get("/{article_id}")
async def get_article(
    article_id: int,
    service: ArticleService = Depends(get_article_service),
) -> ApiResponse[ArticleResponse]:
    article = await service.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return ApiResponse(
        success=True,
        data=ArticleResponse.model_validate(article),
    )


@router.patch("/{article_id}")
async def update_article(
    article_id: int,
    data: ArticleUpdate,
    service: ArticleService = Depends(get_article_service),
) -> ApiResponse[ArticleResponse]:
    article = await service.update(article_id, data)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return ApiResponse(
        success=True,
        data=ArticleResponse.model_validate(article),
    )


@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    service: ArticleService = Depends(get_article_service),
) -> ApiResponse[dict]:
    deleted = await service.delete(article_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Article not found")
    return ApiResponse(success=True, data={"deleted": True})
