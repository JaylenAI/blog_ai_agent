from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()

STYLE_GUIDE_PATH = Path(__file__).resolve().parents[4] / "docs" / "style-guide" / "blog-style.md"


@router.get("/style-guide", response_class=PlainTextResponse)
async def get_style_guide() -> str:
    if not STYLE_GUIDE_PATH.exists():
        return "스타일 가이드 파일을 찾을 수 없습니다."
    return STYLE_GUIDE_PATH.read_text(encoding="utf-8")
