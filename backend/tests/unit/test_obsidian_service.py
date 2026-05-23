import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from app.services.obsidian_service import ObsidianService, format_obsidian_note


def _make_service(
    vault_path: str = "",
    content: str | None = "# Test",
    meta: dict | None = None,
) -> ObsidianService:
    fm = MagicMock()
    fm.read_text.return_value = content
    default_meta = {"title": "Test", "category": "AI", "seo_keywords": ["test"]}
    fm.read_json.return_value = meta or default_meta
    return ObsidianService(fm, vault_path)


def test_vault_not_configured() -> None:
    svc = _make_service(vault_path="")
    assert svc.vault_configured is False
    result = svc.save_article("slug")
    assert result["success"] is False


def test_vault_nonexistent_path() -> None:
    svc = _make_service(vault_path="/nonexistent/vault")
    assert svc.vault_exists is False
    result = svc.save_article("slug")
    assert result["success"] is False


def test_save_article_success() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        svc = _make_service(vault_path=tmpdir)
        result = svc.save_article("slug")

        assert result["success"] is True
        saved = Path(tmpdir) / "Test.md"
        assert saved.exists()
        content = saved.read_text(encoding="utf-8")
        assert "blog/published" in content


def test_save_article_no_content() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        svc = _make_service(vault_path=tmpdir, content=None)
        result = svc.save_article("slug")
        assert result["success"] is False


def test_format_obsidian_note_basic() -> None:
    meta = {"title": "T", "category": "AI", "seo_keywords": ["k1"]}
    result = format_obsidian_note("# Body", meta)
    assert "---" in result
    assert "blog/published" in result
    assert "category/ai" in result
    assert "keyword/k1" in result
    assert "# Body" in result


def test_format_obsidian_note_empty_meta() -> None:
    result = format_obsidian_note("body", {})
    assert "category/uncategorized" in result
