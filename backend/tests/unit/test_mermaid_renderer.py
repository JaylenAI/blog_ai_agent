from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.images.mermaid_renderer import render_all_diagrams, render_mermaid


@pytest.mark.asyncio
async def test_render_mermaid_success(tmp_path: Path) -> None:
    mmd_path = tmp_path / "test.mmd"
    mmd_path.write_text("graph TD\n  A-->B")
    output_path = tmp_path / "output" / "test.png"

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await render_mermaid(mmd_path, output_path)

    assert result is True


@pytest.mark.asyncio
async def test_render_mermaid_failure(tmp_path: Path) -> None:
    mmd_path = tmp_path / "test.mmd"
    mmd_path.write_text("invalid mermaid")
    output_path = tmp_path / "test.png"

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"Parse error")
    mock_proc.returncode = 1

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await render_mermaid(mmd_path, output_path)

    assert result is False


@pytest.mark.asyncio
async def test_render_mermaid_no_mmdc(tmp_path: Path) -> None:
    mmd_path = tmp_path / "test.mmd"
    mmd_path.write_text("graph TD\n  A-->B")
    output_path = tmp_path / "test.png"

    with patch("shutil.which", return_value=None):
        result = await render_mermaid(mmd_path, output_path)

    assert result is False


@pytest.mark.asyncio
async def test_render_mermaid_timeout(tmp_path: Path) -> None:
    mmd_path = tmp_path / "test.mmd"
    mmd_path.write_text("graph TD\n  A-->B")
    output_path = tmp_path / "test.png"

    mock_proc = AsyncMock()
    mock_proc.communicate.side_effect = TimeoutError()

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await render_mermaid(mmd_path, output_path)

    assert result is False


@pytest.mark.asyncio
async def test_render_all_diagrams_no_dir(tmp_path: Path) -> None:
    results = await render_all_diagrams(tmp_path)
    assert results == []


@pytest.mark.asyncio
async def test_render_all_diagrams_success(tmp_path: Path) -> None:
    diagrams_dir = tmp_path / "diagrams"
    diagrams_dir.mkdir()
    (diagrams_dir / "diagram_1.mmd").write_text("graph TD\n  A-->B")
    (diagrams_dir / "diagram_2.mmd").write_text("graph LR\n  X-->Y")

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        results = await render_all_diagrams(tmp_path)

    assert len(results) == 2
    assert all(r["success"] for r in results)
    assert results[0]["source"] == "diagram_1.mmd"
    assert results[0]["output"] == "diagram_1.png"
