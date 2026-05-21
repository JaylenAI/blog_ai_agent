import json
from pathlib import Path

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FileManager:
    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir or settings.sisyphus_path

    def article_dir(self, slug: str) -> Path:
        path = self._base / slug
        path.mkdir(parents=True, exist_ok=True)
        return path

    def images_dir(self, slug: str) -> Path:
        path = self.article_dir(slug) / "images"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_text(self, slug: str, filename: str, content: str) -> Path:
        path = self.article_dir(slug) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.info("Wrote %s (%d bytes)", path, len(content))
        return path

    def write_json(self, slug: str, filename: str, data: dict | list) -> Path:
        content = json.dumps(data, ensure_ascii=False, indent=2)
        return self.write_text(slug, filename, content)

    def read_text(self, slug: str, filename: str) -> str | None:
        path = self.article_dir(slug) / filename
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def read_json(self, slug: str, filename: str) -> dict | list | None:
        content = self.read_text(slug, filename)
        if content is None:
            return None
        return json.loads(content)

    def exists(self, slug: str, filename: str) -> bool:
        return (self.article_dir(slug) / filename).exists()

    def list_files(self, slug: str) -> list[str]:
        path = self._base / slug
        if not path.exists():
            return []
        return sorted(f.name for f in path.iterdir() if f.is_file())
