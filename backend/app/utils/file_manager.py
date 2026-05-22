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

    def list_images(self, slug: str) -> list[str]:
        images = self.images_dir(slug)
        if not images.exists():
            return []
        suffixes = {".png", ".svg", ".jpg", ".jpeg"}
        return sorted(
            f.name for f in images.iterdir()
            if f.is_file() and f.suffix.lower() in suffixes
        )

    def diagrams_dir(self, slug: str) -> Path:
        path = self.article_dir(slug) / "diagrams"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_diagrams(self, slug: str) -> list[str]:
        diagrams = self.article_dir(slug) / "diagrams"
        if not diagrams.exists():
            return []
        return sorted(
            f.name for f in diagrams.iterdir()
            if f.is_file() and f.suffix.lower() == ".mmd"
        )

    def delete_article_dir(self, slug: str) -> bool:
        import shutil

        path = self._base / slug
        if not path.exists():
            return False
        shutil.rmtree(path)
        logger.info("Deleted article directory: %s", path)
        return True

    def _versions_dir(self, slug: str) -> Path:
        path = self.article_dir(slug) / "versions"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def backup_content(self, slug: str, max_versions: int = 10) -> str | None:
        import time

        content = self.read_text(slug, "final.md")
        if not content:
            return None

        versions_dir = self._versions_dir(slug)
        version_id = str(int(time.time() * 1000))
        version_file = versions_dir / f"{version_id}.md"
        version_file.write_text(content, encoding="utf-8")

        existing = sorted(versions_dir.glob("*.md"), key=lambda f: f.stem)
        while len(existing) > max_versions:
            oldest = existing.pop(0)
            oldest.unlink()
            logger.info("Removed old version: %s", oldest)

        logger.info("Backed up content to version %s", version_id)
        return version_id

    def list_versions(self, slug: str) -> list[dict]:
        import time

        versions_dir = self._base / slug / "versions"
        if not versions_dir.exists():
            return []

        result = []
        for f in sorted(versions_dir.glob("*.md"), key=lambda f: f.stem, reverse=True):
            try:
                ts = int(f.stem) / 1000
                content = f.read_text(encoding="utf-8")
                result.append({
                    "version_id": f.stem,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)),
                    "size": len(content),
                    "word_count": len(content.replace(" ", "").replace("\n", "")),
                })
            except (ValueError, OSError):
                continue
        return result

    def get_version_content(self, slug: str, version_id: str) -> str | None:
        safe_id = version_id.replace("..", "").replace("/", "")
        version_file = self._base / slug / "versions" / f"{safe_id}.md"
        if not version_file.exists():
            return None
        return version_file.read_text(encoding="utf-8")

    def restore_version(self, slug: str, version_id: str) -> bool:
        content = self.get_version_content(slug, version_id)
        if content is None:
            return False
        self.backup_content(slug)
        self.write_text(slug, "final.md", content)
        logger.info("Restored version %s for %s", version_id, slug)
        return True
