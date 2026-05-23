"""PlaywrightRenderer 유닛 테스트."""

from pathlib import Path
from unittest.mock import patch

import pytest

from app.images.playwright_renderer import (
    _COMPARISON_TEMPLATE,
    _INFOGRAPHIC_TEMPLATE,
    _THUMBNAIL_TEMPLATE,
    DARK_THEME,
    LIGHT_THEME,
    _escape,
    render_comparison,
    render_infographic,
    render_thumbnail,
)

_PATCH_TARGET = "app.images.playwright_renderer._take_screenshot"


def test_escape_html_entities():
    assert _escape("a & b") == "a &amp; b"
    assert _escape("<script>") == "&lt;script&gt;"
    assert _escape('"hello"') == "&quot;hello&quot;"
    assert _escape("normal text") == "normal text"


def test_dark_theme_has_required_keys():
    required = {
        "bg", "title_color", "sub_color", "foot_color",
        "accent", "item_bg", "border",
    }
    assert required.issubset(set(DARK_THEME.keys()))


def test_light_theme_has_required_keys():
    required = {
        "bg", "title_color", "sub_color", "foot_color",
        "accent", "item_bg", "border",
    }
    assert required.issubset(set(LIGHT_THEME.keys()))


def test_thumbnail_template_renders_without_error():
    html = _THUMBNAIL_TEMPLATE.format(
        title="테스트 제목",
        category="Tech",
        subtitle="부제목입니다",
        author="Jaylen",
        blog_name="AI의 정석",
        **DARK_THEME,
    )
    assert "테스트 제목" in html
    assert "Tech" in html
    assert "<html>" in html


def test_infographic_template_renders():
    items_html = (
        '<div class="info-item">'
        '<div class="info-item-num">01</div></div>'
    )
    html = _INFOGRAPHIC_TEMPLATE.format(
        title="인포그래픽",
        items_html=items_html,
        cols=2,
        height=400,
        **DARK_THEME,
    )
    assert "인포그래픽" in html
    assert "info-item-num" in html


def test_comparison_template_renders():
    html = _COMPARISON_TEMPLATE.format(
        title="비교표",
        headers_html="<th>항목</th><th>A</th><th>B</th>",
        rows_html="<tr><td>속도</td><td>빠름</td><td>느림</td></tr>",
        height=300,
        **DARK_THEME,
    )
    assert "비교표" in html
    assert "<th>항목</th>" in html


async def _fake_ok(
    html: str, output_path: Path,
    width: int = 1200, height: int = 630,
) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"\x89PNG" + b"\x00" * 200)
    return True


async def _fake_fail(
    html: str, output_path: Path,
    width: int = 1200, height: int = 630,
) -> bool:
    return False


@pytest.mark.asyncio
async def test_render_thumbnail_success(tmp_path: Path):
    with patch(_PATCH_TARGET, side_effect=_fake_ok):
        result = await render_thumbnail(
            tmp_path / "thumb.png",
            title="MCP 서버 구축하기",
            category="Tutorial",
            subtitle="처음부터 끝까지",
        )
    assert result is True
    assert (tmp_path / "thumb.png").exists()


@pytest.mark.asyncio
async def test_render_thumbnail_failure(tmp_path: Path):
    with patch(_PATCH_TARGET, side_effect=_fake_fail):
        result = await render_thumbnail(
            tmp_path / "thumb.png",
            title="실패 테스트",
        )
    assert result is False


@pytest.mark.asyncio
async def test_render_thumbnail_light_theme(tmp_path: Path):
    with patch(_PATCH_TARGET, side_effect=_fake_ok):
        result = await render_thumbnail(
            tmp_path / "light.png",
            title="라이트 모드",
            theme="light",
        )
    assert result is True


@pytest.mark.asyncio
async def test_render_infographic_success(tmp_path: Path):
    with patch(_PATCH_TARGET, side_effect=_fake_ok):
        result = await render_infographic(
            tmp_path / "info.png",
            title="핵심 개념 정리",
            items=[
                {"title": "개념 1", "desc": "설명 1"},
                {"title": "개념 2", "desc": "설명 2"},
                {"title": "개념 3", "desc": "설명 3"},
            ],
        )
    assert result is True


@pytest.mark.asyncio
async def test_render_infographic_with_3_cols(tmp_path: Path):
    with patch(_PATCH_TARGET, side_effect=_fake_ok):
        result = await render_infographic(
            tmp_path / "info3.png",
            title="3열 레이아웃",
            items=[
                {"title": f"항목 {i}", "desc": f"설명 {i}"}
                for i in range(6)
            ],
            cols=3,
        )
    assert result is True


@pytest.mark.asyncio
async def test_render_comparison_success(tmp_path: Path):
    with patch(_PATCH_TARGET, side_effect=_fake_ok):
        result = await render_comparison(
            tmp_path / "comp.png",
            title="프레임워크 비교",
            headers=["항목", "React", "Vue"],
            rows=[
                ["학습곡선", "중간", "낮음"],
                ["생태계", "풍부", "성장 중"],
            ],
        )
    assert result is True


@pytest.mark.asyncio
async def test_render_comparison_light_theme(tmp_path: Path):
    with patch(_PATCH_TARGET, side_effect=_fake_ok):
        result = await render_comparison(
            tmp_path / "comp_light.png",
            title="비교표 라이트",
            headers=["A", "B"],
            rows=[["1", "2"]],
            theme="light",
        )
    assert result is True
