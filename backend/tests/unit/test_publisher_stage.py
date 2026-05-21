import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.pipeline.base import StageInput
from app.pipeline.stages.s6_publisher import PublisherStage, _format_obsidian_note

MOCK_CONTENT = "# AI란 무엇인가?\n\n## 1. 들어가며\n\n본문입니다."

MOCK_META = {
    "title": "AI란 무엇인가?",
    "category": "AI/ML",
    "seo_keywords": ["AI", "인공지능"],
}


def _make_stage(
    content: str | None = None,
    meta: dict | None = None,
    vault_path: str = "",
) -> tuple[PublisherStage, MagicMock]:
    mock_fm = MagicMock()

    def read_text_effect(slug: str, filename: str) -> str | None:
        if filename == "final.md":
            return MOCK_CONTENT if content is None else content
        return None

    def read_json_effect(slug: str, filename: str) -> dict | list | None:
        if filename == "meta.json":
            return meta if meta is not None else MOCK_META
        return None

    mock_fm.read_text.side_effect = read_text_effect
    mock_fm.read_json.side_effect = read_json_effect
    mock_fm.article_dir.return_value = Path("/tmp/test-slug")
    mock_fm.write_text.return_value = Path("/tmp/test-slug/tistory.html")

    return PublisherStage(mock_fm, obsidian_vault_path=vault_path), mock_fm


def _make_input() -> StageInput:
    return StageInput(
        article_id=1,
        slug="ai란-무엇인가",
        topic="AI란 무엇인가?",
    )


async def test_publisher_name() -> None:
    stage, _ = _make_stage()
    assert stage.name == "publisher"


@patch("app.pipeline.stages.s6_publisher.render_all_diagrams", return_value=[])
async def test_publisher_success_no_vault(mock_render: MagicMock) -> None:
    stage, mock_fm = _make_stage()
    result = await stage.execute(_make_input())

    assert result.success is True
    assert result.data["obsidian_saved"] is False
    assert result.data["tistory_ready"] is True
    assert "content_path" in result.data
    assert "html_path" in result.data
    mock_fm.write_text.assert_called()


async def test_publisher_no_final_md() -> None:
    stage, _ = _make_stage()
    stage._fm.read_text.side_effect = lambda s, f: None

    result = await stage.execute(_make_input())

    assert result.success is False
    assert "final.md" in result.error


@patch("app.pipeline.stages.s6_publisher.render_all_diagrams", return_value=[])
async def test_publisher_saves_to_obsidian(mock_render: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        stage, _ = _make_stage(vault_path=tmpdir)
        result = await stage.execute(_make_input())

        assert result.success is True
        assert result.data["obsidian_saved"] is True

        saved_file = Path(tmpdir) / "AI란 무엇인가?.md"
        assert saved_file.exists()

        content = saved_file.read_text(encoding="utf-8")
        assert "tags:" in content
        assert "blog/published" in content
        assert "AI란 무엇인가?" in content


@patch("app.pipeline.stages.s6_publisher.render_all_diagrams", return_value=[])
async def test_publisher_obsidian_nonexistent_vault(mock_render: MagicMock) -> None:
    stage, _ = _make_stage(vault_path="/nonexistent/path/vault")
    result = await stage.execute(_make_input())

    assert result.success is True
    assert result.data["obsidian_saved"] is False


@patch(
    "app.pipeline.stages.s6_publisher.render_all_diagrams",
    return_value=[{"source": "d1.mmd", "output": "d1.png", "success": True}],
)
async def test_publisher_renders_diagrams(mock_render: MagicMock) -> None:
    stage, _ = _make_stage()
    result = await stage.execute(_make_input())

    assert result.success is True
    assert result.data["diagrams_rendered"] == 1


@patch("app.pipeline.stages.s6_publisher.render_all_diagrams", return_value=[])
async def test_publisher_generates_html(mock_render: MagicMock) -> None:
    stage, mock_fm = _make_stage()
    result = await stage.execute(_make_input())

    assert result.success is True
    write_calls = mock_fm.write_text.call_args_list
    html_call = [c for c in write_calls if "tistory.html" in str(c)]
    assert len(html_call) == 1


def test_format_obsidian_note() -> None:
    result = _format_obsidian_note("# 제목\n\n본문", MOCK_META)

    assert "---" in result
    assert "blog/published" in result
    assert "category/ai-ml" in result
    assert "keyword/AI" in result
    assert "keyword/인공지능" in result
    assert 'title: "AI란 무엇인가?"' in result
    assert "# 제목\n\n본문" in result


def test_format_obsidian_note_empty_meta() -> None:
    result = _format_obsidian_note("본문", {})

    assert "---" in result
    assert "category/uncategorized" in result
    assert "본문" in result
