from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.images.image_generator import ImageGenerator, sanitize_svg, validate_image_file

# --- validate_image_file ---


def test_validate_image_file_not_exists(tmp_path: Path) -> None:
    path = tmp_path / "no_such_file.svg"
    assert validate_image_file(path) is False


def test_validate_image_file_too_small(tmp_path: Path) -> None:
    path = tmp_path / "tiny.svg"
    path.write_text("x", encoding="utf-8")
    assert validate_image_file(path) is False


def test_validate_svg_valid(tmp_path: Path) -> None:
    path = tmp_path / "good.svg"
    content = "<svg xmlns='http://www.w3.org/2000/svg'><rect/></svg>" + ("x" * 50)
    path.write_text(content, encoding="utf-8")
    assert validate_image_file(path) is True


def test_validate_svg_missing_tags(tmp_path: Path) -> None:
    path = tmp_path / "bad.svg"
    path.write_text("x" * 100, encoding="utf-8")
    assert validate_image_file(path) is False


def test_validate_png_valid(tmp_path: Path) -> None:
    path = tmp_path / "good.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    assert validate_image_file(path) is True


def test_validate_png_invalid_header(tmp_path: Path) -> None:
    path = tmp_path / "bad.png"
    path.write_bytes(b"NOT_A_PNG" + b"\x00" * 100)
    assert validate_image_file(path) is False


def test_validate_other_extension(tmp_path: Path) -> None:
    path = tmp_path / "image.jpg"
    path.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)
    assert validate_image_file(path) is True


def test_validate_other_extension_empty(tmp_path: Path) -> None:
    path = tmp_path / "empty.jpg"
    path.write_bytes(b"")
    assert validate_image_file(path) is False


# --- sanitize_svg ---


def test_sanitize_svg_non_svg(tmp_path: Path) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(b"\x89PNG")
    sanitize_svg(path)


def test_sanitize_svg_not_exists(tmp_path: Path) -> None:
    path = tmp_path / "missing.svg"
    sanitize_svg(path)


def test_sanitize_svg_clean(tmp_path: Path) -> None:
    path = tmp_path / "clean.svg"
    content = "<svg><rect/></svg>"
    path.write_text(content, encoding="utf-8")
    sanitize_svg(path)
    assert path.read_text(encoding="utf-8") == content


def test_sanitize_svg_removes_script(tmp_path: Path) -> None:
    path = tmp_path / "dirty.svg"
    content = '<svg><script>alert("xss")</script><rect/></svg>'
    path.write_text(content, encoding="utf-8")
    sanitize_svg(path)
    result = path.read_text(encoding="utf-8")
    assert "<script" not in result
    assert "<rect/>" in result


def test_sanitize_svg_removes_event_handlers(tmp_path: Path) -> None:
    path = tmp_path / "events.svg"
    content = '<svg><rect onclick="evil()" onload="bad()"/></svg>'
    path.write_text(content, encoding="utf-8")
    sanitize_svg(path)
    result = path.read_text(encoding="utf-8")
    assert "onclick" not in result
    assert "onload" not in result


def test_sanitize_svg_removes_onerror_onmouseover(tmp_path: Path) -> None:
    path = tmp_path / "more_events.svg"
    content = '<svg><image onerror="x()" onmouseover="y()"/></svg>'
    path.write_text(content, encoding="utf-8")
    sanitize_svg(path)
    result = path.read_text(encoding="utf-8")
    assert "onerror" not in result
    assert "onmouseover" not in result


# --- ImageGenerator ---


@pytest.fixture
def mock_claude() -> AsyncMock:
    claude = AsyncMock()
    claude.run_json = AsyncMock(
        return_value={
            "images": [
                {
                    "filename": "arch.svg",
                    "type": "svg",
                    "description": "architecture diagram",
                    "alt": "Architecture",
                    "insert_after_heading": "Overview",
                }
            ]
        }
    )
    claude.run = AsyncMock(return_value=MagicMock(text="done"))
    return claude


@pytest.fixture
def mock_fm(tmp_path: Path) -> MagicMock:
    fm = MagicMock()
    fm.write_json = MagicMock()
    fm.images_dir = MagicMock(return_value=tmp_path)
    return fm


@pytest.fixture
def generator(mock_claude: AsyncMock, mock_fm: MagicMock) -> ImageGenerator:
    with patch("app.images.image_generator.settings") as mock_settings:
        mock_settings.image_generation_timeout = 120
        mock_settings.max_images_per_article = 4
        mock_settings.image_allowed_tools = "Write,Bash"
        return ImageGenerator(mock_claude, mock_fm)


async def test_plan_images(
    generator: ImageGenerator, mock_claude: AsyncMock, mock_fm: MagicMock
) -> None:
    result = await generator.plan_images("test-slug", "content", "AI topic")

    assert len(result) == 1
    assert result[0]["filename"] == "arch.svg"
    mock_claude.run_json.assert_awaited_once()
    mock_fm.write_json.assert_called_once_with("test-slug", "image_plan.json", result)


async def test_plan_images_truncates_to_max(
    mock_claude: AsyncMock, mock_fm: MagicMock
) -> None:
    mock_claude.run_json.return_value = {
        "images": [{"filename": f"img{i}.svg"} for i in range(10)]
    }
    with patch("app.images.image_generator.settings") as mock_settings:
        mock_settings.image_generation_timeout = 120
        mock_settings.max_images_per_article = 2
        mock_settings.image_allowed_tools = "Write,Bash"
        gen = ImageGenerator(mock_claude, mock_fm)

    result = await gen.plan_images("slug", "content", "topic")
    assert len(result) == 2


async def test_generate_image_success(
    generator: ImageGenerator, mock_fm: MagicMock, tmp_path: Path
) -> None:
    svg_file = tmp_path / "arch.svg"
    svg_content = "<svg xmlns='http://www.w3.org/2000/svg'><rect/></svg>" + ("x" * 50)
    svg_file.write_text(svg_content, encoding="utf-8")

    spec = {
        "filename": "arch.svg",
        "type": "svg",
        "description": "architecture",
        "alt": "Architecture",
        "insert_after_heading": "Overview",
    }
    result = await generator.generate_image("test-slug", spec, "topic")

    assert result["success"] is True
    assert result["filename"] == "arch.svg"
    assert result["alt"] == "Architecture"
    assert result["insert_after_heading"] == "Overview"


async def test_generate_image_validation_fails(
    generator: ImageGenerator, mock_fm: MagicMock, tmp_path: Path
) -> None:
    spec = {"filename": "missing.svg", "type": "svg", "alt": "Missing"}
    result = await generator.generate_image("test-slug", spec, "topic")

    assert result["success"] is False


async def test_generate_image_runtime_error(
    generator: ImageGenerator, mock_claude: AsyncMock, mock_fm: MagicMock
) -> None:
    mock_claude.run.side_effect = RuntimeError("Claude CLI crashed")

    spec = {"filename": "fail.svg", "type": "svg", "alt": "Fail"}
    result = await generator.generate_image("test-slug", spec, "topic")

    assert result["success"] is False
    assert result["error"] == "Claude CLI crashed"


async def test_generate_image_timeout_error(
    generator: ImageGenerator, mock_claude: AsyncMock, mock_fm: MagicMock
) -> None:
    mock_claude.run.side_effect = TimeoutError("timed out")

    spec = {"filename": "timeout.svg", "type": "svg", "alt": "Timeout"}
    result = await generator.generate_image("test-slug", spec, "topic")

    assert result["success"] is False
    assert "timed out" in result["error"]


async def test_generate_image_default_values(
    generator: ImageGenerator, mock_fm: MagicMock, tmp_path: Path
) -> None:
    """spec에 filename, type, alt 등이 없을 때 기본값 사용"""
    svg_file = tmp_path / "image.svg"
    svg_content = "<svg xmlns='http://www.w3.org/2000/svg'><rect/></svg>" + ("x" * 50)
    svg_file.write_text(svg_content, encoding="utf-8")

    result = await generator.generate_image("test-slug", {}, "topic")

    assert result["filename"] == "image.svg"
    assert result["type"] == "svg"


async def test_generate_all_success(
    generator: ImageGenerator,
    mock_claude: AsyncMock,
    mock_fm: MagicMock,
    tmp_path: Path,
) -> None:
    svg_file = tmp_path / "arch.svg"
    svg_content = "<svg xmlns='http://www.w3.org/2000/svg'><rect/></svg>" + ("x" * 50)
    svg_file.write_text(svg_content, encoding="utf-8")

    results = await generator.generate_all("test-slug", "content", "topic")

    assert len(results) == 1
    assert results[0]["success"] is True
    assert mock_fm.write_json.call_count == 2  # plan + results


async def test_generate_all_empty_plan(
    mock_claude: AsyncMock, mock_fm: MagicMock
) -> None:
    mock_claude.run_json.return_value = {"images": []}
    with patch("app.images.image_generator.settings") as mock_settings:
        mock_settings.image_generation_timeout = 120
        mock_settings.max_images_per_article = 4
        mock_settings.image_allowed_tools = "Write,Bash"
        gen = ImageGenerator(mock_claude, mock_fm)

    results = await gen.generate_all("slug", "content", "topic")
    assert results == []


async def test_generate_all_mixed_results(
    mock_claude: AsyncMock, mock_fm: MagicMock, tmp_path: Path
) -> None:
    mock_claude.run_json.return_value = {
        "images": [
            {"filename": "ok.svg", "type": "svg", "alt": "OK"},
            {"filename": "fail.svg", "type": "svg", "alt": "Fail"},
        ]
    }
    with patch("app.images.image_generator.settings") as mock_settings:
        mock_settings.image_generation_timeout = 120
        mock_settings.max_images_per_article = 4
        mock_settings.image_allowed_tools = "Write,Bash"
        gen = ImageGenerator(mock_claude, mock_fm)
        gen._fm.images_dir = MagicMock(return_value=tmp_path)

    ok_file = tmp_path / "ok.svg"
    ok_file.write_text(
        "<svg xmlns='http://www.w3.org/2000/svg'><rect/></svg>" + ("x" * 50),
        encoding="utf-8",
    )

    results = await gen.generate_all("slug", "content", "topic")

    assert len(results) == 2
    assert results[0]["success"] is True
    assert results[1]["success"] is False
    mock_fm.write_json.assert_any_call("slug", "image_results.json", results)
