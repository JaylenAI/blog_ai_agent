from datetime import datetime
from pathlib import Path

from app.utils.file_manager import FileManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ObsidianService:
    def __init__(self, file_manager: FileManager, vault_path: str = "") -> None:
        self._fm = file_manager
        self._vault_path = vault_path

    @property
    def vault_configured(self) -> bool:
        return bool(self._vault_path)

    @property
    def vault_exists(self) -> bool:
        return self.vault_configured and Path(self._vault_path).exists()

    def save_article(self, slug: str) -> dict:
        content = self._fm.read_text(slug, "final.md")
        if not content:
            return {"success": False, "error": "final.md를 찾을 수 없습니다"}

        meta = self._fm.read_json(slug, "meta.json") or {}

        if not self._vault_path:
            return {"success": False, "error": "Obsidian vault 경로가 설정되지 않았습니다"}

        vault = Path(self._vault_path)
        if not vault.exists():
            return {"success": False, "error": f"Obsidian vault 경로가 존재하지 않습니다: {vault}"}

        title = meta.get("title", slug)
        safe_title = title.replace("/", "-").replace("\\", "-")
        target = vault / f"{safe_title}.md"

        obsidian_content = format_obsidian_note(content, meta)
        target.write_text(obsidian_content, encoding="utf-8")

        logger.info("Obsidian 저장 완료: %s", target)
        return {"success": True, "path": str(target)}


def format_obsidian_note(content: str, meta: dict) -> str:
    category = meta.get("category", "uncategorized").lower().replace("/", "-")
    title = meta.get("title", "")
    today = datetime.now().strftime("%Y-%m-%d")

    keywords = meta.get("seo_keywords", [])
    keyword_tags = "\n".join(f"  - keyword/{kw}" for kw in keywords[:5])

    frontmatter = f"""---
tags:
  - blog/published
  - category/{category}
{keyword_tags}
date: {today}
title: "{title}"
status: published
---

"""
    return frontmatter + content
