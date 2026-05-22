import mimetypes

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, Response

from app.dependencies import get_article_service, get_file_manager
from app.schemas.article import (
    ArticleCreate,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
)
from app.schemas.common import ApiResponse
from app.services.article_service import ArticleService
from app.utils.file_manager import FileManager

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


@router.get("/{article_id}/content")
async def get_article_content(
    article_id: int,
    service: ArticleService = Depends(get_article_service),
    fm: FileManager = Depends(get_file_manager),
) -> PlainTextResponse:
    article = await service.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    content = fm.read_text(article.slug, "final.md")
    if content is None:
        raise HTTPException(status_code=404, detail="Content not generated yet")
    return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")


@router.get("/{article_id}/html")
async def get_article_html(
    article_id: int,
    service: ArticleService = Depends(get_article_service),
    fm: FileManager = Depends(get_file_manager),
) -> ApiResponse[str]:
    article = await service.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    html = fm.read_text(article.slug, "tistory.html")
    if html is None:
        raise HTTPException(status_code=404, detail="HTML not generated yet")
    return ApiResponse(success=True, data=html)


@router.get("/{article_id}/images")
async def list_article_images(
    article_id: int,
    service: ArticleService = Depends(get_article_service),
    fm: FileManager = Depends(get_file_manager),
) -> ApiResponse[list[str]]:
    article = await service.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    images = fm.list_images(article.slug)
    return ApiResponse(success=True, data=images)


@router.get("/{article_id}/images/{filename}")
async def get_article_image(
    article_id: int,
    filename: str,
    service: ArticleService = Depends(get_article_service),
    fm: FileManager = Depends(get_file_manager),
) -> Response:
    article = await service.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    safe_name = filename.replace("..", "").replace("/", "").replace("\\", "")
    image_path = fm.images_dir(article.slug) / safe_name
    if not image_path.exists() or not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")

    content_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
    return Response(
        content=image_path.read_bytes(),
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=3600"},
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
