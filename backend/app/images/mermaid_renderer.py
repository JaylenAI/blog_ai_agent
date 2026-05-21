import asyncio
import shutil
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)

MERMAID_THEME = "dark"
MERMAID_WIDTH = 1200
MERMAID_BG = "transparent"


async def render_mermaid(
    mmd_path: Path,
    output_path: Path,
    *,
    width: int = MERMAID_WIDTH,
    theme: str = MERMAID_THEME,
    background: str = MERMAID_BG,
) -> bool:
    mmdc = shutil.which("mmdc")
    if not mmdc:
        logger.warning("mmdc를 찾을 수 없습니다 — Mermaid 렌더링 건너뜀")
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)

    args = [
        mmdc,
        "-i", str(mmd_path),
        "-o", str(output_path),
        "-w", str(width),
        "-t", theme,
        "-b", background,
        "--quiet",
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr_bytes = await asyncio.wait_for(
            process.communicate(), timeout=30,
        )

        if process.returncode != 0:
            error_msg = stderr_bytes.decode("utf-8", errors="replace")
            logger.warning(
                "Mermaid 렌더링 실패 (%s): %s",
                mmd_path.name,
                error_msg[:200],
            )
            return False

        logger.info("Mermaid 렌더링 완료: %s → %s", mmd_path.name, output_path.name)
        return True

    except TimeoutError:
        logger.warning("Mermaid 렌더링 타임아웃: %s", mmd_path.name)
        return False


async def render_all_diagrams(
    slug_dir: Path,
) -> list[dict]:
    diagrams_dir = slug_dir / "diagrams"
    if not diagrams_dir.exists():
        return []

    images_dir = slug_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    mmd_files = sorted(diagrams_dir.glob("*.mmd"))

    for mmd_file in mmd_files:
        png_name = mmd_file.stem + ".png"
        png_path = images_dir / png_name

        success = await render_mermaid(mmd_file, png_path)
        results.append({
            "source": mmd_file.name,
            "output": png_name,
            "success": success,
        })

    rendered = sum(1 for r in results if r["success"])
    logger.info("다이어그램 렌더링: %d/%d 성공", rendered, len(results))
    return results
