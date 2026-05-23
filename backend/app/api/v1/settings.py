import json
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.config import settings
from app.dependencies import get_article_service, get_file_manager
from app.schemas.article import ArticleUpdate
from app.schemas.common import ApiResponse
from app.services.article_service import ArticleService
from app.utils.file_manager import FileManager

router = APIRouter()

STYLE_GUIDE_PATH = Path(__file__).resolve().parents[4] / "docs" / "style-guide" / "blog-style.md"
SETTINGS_FILE = Path(__file__).resolve().parents[4] / "data" / "user-settings.json"


def _load_user_settings() -> dict:
    if SETTINGS_FILE.exists():
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    return {}


def _save_user_settings(data: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/style-guide", response_class=PlainTextResponse)
async def get_style_guide() -> str:
    if not STYLE_GUIDE_PATH.exists():
        return "스타일 가이드 파일을 찾을 수 없습니다."
    return STYLE_GUIDE_PATH.read_text(encoding="utf-8")


class ObsidianSettings(BaseModel):
    vault_path: str = ""
    frontmatter_tags: list[str] = ["blog/published"]
    auto_save: bool = False


@router.get("/obsidian")
async def get_obsidian_settings() -> ApiResponse[ObsidianSettings]:
    user = _load_user_settings()
    obsidian = user.get("obsidian", {})
    return ApiResponse(
        success=True,
        data=ObsidianSettings(
            vault_path=obsidian.get("vault_path", settings.obsidian_vault_path),
            frontmatter_tags=obsidian.get("frontmatter_tags", ["blog/published"]),
            auto_save=obsidian.get("auto_save", False),
        ),
    )


@router.put("/obsidian")
async def update_obsidian_settings(data: ObsidianSettings) -> ApiResponse[ObsidianSettings]:
    user = _load_user_settings()
    user["obsidian"] = data.model_dump()
    _save_user_settings(user)
    return ApiResponse(success=True, data=data)


class GeneralSettings(BaseModel):
    tistory_blog_url: str = ""
    stage_timeout: int = 600
    image_generation_enabled: bool = True
    max_images_per_article: int = 4
    log_level: str = "INFO"


@router.get("/general")
async def get_general_settings() -> ApiResponse[GeneralSettings]:
    user = _load_user_settings()
    general = user.get("general", {})
    return ApiResponse(
        success=True,
        data=GeneralSettings(
            tistory_blog_url=general.get("tistory_blog_url", settings.tistory_blog_url),
            stage_timeout=general.get("stage_timeout", settings.stage_timeout),
            image_generation_enabled=general.get(
                "image_generation_enabled",
                settings.image_generation_enabled,
            ),
            max_images_per_article=general.get(
                "max_images_per_article",
                settings.max_images_per_article,
            ),
            log_level=general.get("log_level", settings.log_level),
        ),
    )


@router.put("/general")
async def update_general_settings(data: GeneralSettings) -> ApiResponse[GeneralSettings]:
    user = _load_user_settings()
    user["general"] = data.model_dump()
    _save_user_settings(user)
    return ApiResponse(success=True, data=data)


class BatchUpdateRequest(BaseModel):
    article_ids: list[int]
    category: str | None = None
    tags: list[str] | None = None
    status: str | None = None


@router.post("/batch-update")
async def batch_update_articles(
    data: BatchUpdateRequest,
    service: ArticleService = Depends(get_article_service),
    fm: FileManager = Depends(get_file_manager),
) -> ApiResponse[dict]:
    updated = 0
    for aid in data.article_ids:
        article = await service.get_by_id(aid)
        if not article:
            continue

        update_data: dict = {}
        if data.category is not None:
            update_data["category"] = data.category
        if data.status is not None:
            update_data["status"] = data.status

        if update_data:
            await service.update(aid, ArticleUpdate(**update_data))

        if data.tags is not None:
            meta = fm.read_json(article.slug, "meta.json")
            if isinstance(meta, dict):
                meta["seo_keywords"] = data.tags
                fm.write_json(article.slug, "meta.json", meta)

        updated += 1

    return ApiResponse(success=True, data={"updated": updated})
