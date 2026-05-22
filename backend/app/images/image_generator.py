from pathlib import Path

from app.claude.client import ClaudeClient
from app.claude.prompts.image_generator import ImageGeneratorPrompt
from app.claude.prompts.image_planner import ImagePlannerPrompt
from app.config import settings
from app.utils.file_manager import FileManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


def validate_image_file(path: Path) -> bool:
    if not path.exists():
        return False
    if path.stat().st_size < 50:
        return False
    if path.suffix == ".svg":
        content = path.read_text(encoding="utf-8", errors="replace")
        return "<svg" in content and "</svg>" in content
    if path.suffix == ".png":
        header = path.read_bytes()[:8]
        return header[:4] == b"\x89PNG"
    return path.stat().st_size > 0


def sanitize_svg(path: Path) -> None:
    if path.suffix != ".svg" or not path.exists():
        return
    content = path.read_text(encoding="utf-8", errors="replace")
    dirty = False
    if "<script" in content.lower():
        import re
        content = re.sub(
            r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE
        )
        dirty = True
    for attr in ("onclick", "onload", "onerror", "onmouseover"):
        if attr in content.lower():
            import re
            content = re.sub(
                rf'\s{attr}\s*=\s*"[^"]*"', "", content, flags=re.IGNORECASE
            )
            dirty = True
    if dirty:
        path.write_text(content, encoding="utf-8")
        logger.warning("SVG sanitized: %s", path.name)


class ImageGenerator:
    def __init__(self, claude: ClaudeClient, file_manager: FileManager) -> None:
        self._claude = claude
        self._fm = file_manager
        self._planner = ImagePlannerPrompt()
        self._gen_prompt = ImageGeneratorPrompt()
        self._timeout = settings.image_generation_timeout
        self._max_images = settings.max_images_per_article
        self._allowed_tools = settings.image_allowed_tools.split(",")

    async def plan_images(
        self, slug: str, content: str, topic: str
    ) -> list[dict]:
        response = await self._claude.run_json(
            self._planner.render(content=content, topic=topic),
            timeout=self._timeout,
        )
        plan = response.get("images", [])
        plan = plan[: self._max_images]
        self._fm.write_json(slug, "image_plan.json", plan)
        logger.info("이미지 계획 수립: %d장 (%s)", len(plan), slug)
        return plan

    async def generate_image(
        self, slug: str, spec: dict, topic: str
    ) -> dict:
        images_dir = self._fm.images_dir(slug)
        filename = spec.get("filename", "image.svg")

        try:
            await self._claude.run(
                self._gen_prompt.render(
                    image_type=spec.get("type", "svg"),
                    filename=filename,
                    description=spec.get("description", ""),
                    topic=topic,
                    output_dir=str(images_dir),
                ),
                timeout=self._timeout,
                allowed_tools=self._allowed_tools,
                add_dir=str(images_dir),
            )
        except (RuntimeError, TimeoutError) as e:
            logger.warning("이미지 생성 실패 (%s): %s", filename, e)
            return {
                "filename": filename,
                "type": spec.get("type", "svg"),
                "alt": spec.get("alt", ""),
                "success": False,
                "error": str(e),
            }

        generated_path = images_dir / filename
        success = validate_image_file(generated_path)

        if success:
            sanitize_svg(generated_path)
            logger.info("이미지 생성 성공: %s", filename)
        else:
            logger.warning("이미지 파일 검증 실패: %s", filename)

        return {
            "filename": filename,
            "type": spec.get("type", "svg"),
            "alt": spec.get("alt", ""),
            "insert_after_heading": spec.get("insert_after_heading", ""),
            "success": success,
        }

    async def generate_all(
        self, slug: str, content: str, topic: str
    ) -> list[dict]:
        plan = await self.plan_images(slug, content, topic)
        if not plan:
            logger.info("이미지 계획 없음 — 건너뜀")
            return []

        results: list[dict] = []
        for spec in plan:
            result = await self.generate_image(slug, spec, topic)
            results.append(result)

        self._fm.write_json(slug, "image_results.json", results)
        succeeded = sum(1 for r in results if r.get("success"))
        logger.info(
            "이미지 생성 완료: %d/%d 성공 (%s)",
            succeeded, len(results), slug,
        )
        return results
