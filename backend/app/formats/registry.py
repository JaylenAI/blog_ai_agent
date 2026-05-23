from __future__ import annotations

from pathlib import Path

import yaml

from app.exceptions import NotFoundError
from app.formats.schema import FormatSpec, FormatSuggestion, FormatSummary
from app.utils.logger import get_logger

logger = get_logger(__name__)

_DEFINITIONS_DIR = Path(__file__).parent / "definitions"


class FormatRegistry:
    def __init__(self) -> None:
        self._formats: dict[str, FormatSpec] = {}

    def load_all(self, definitions_dir: Path | None = None) -> None:
        source = definitions_dir or _DEFINITIONS_DIR
        self._formats.clear()

        if not source.exists():
            logger.warning("형식 정의 디렉토리 없음: %s", source)
            return

        for path in sorted(source.glob("*.yaml")):
            try:
                raw = yaml.safe_load(path.read_text(encoding="utf-8"))
                if not isinstance(raw, dict):
                    continue
                spec = FormatSpec(**raw)
                self._formats[spec.id] = spec
                logger.debug("형식 로딩: %s (%s)", spec.id, spec.name)
            except Exception as e:
                logger.error("형식 파일 로딩 실패 %s: %s", path.name, e)

        logger.info("총 %d개 형식 로딩 완료", len(self._formats))

    def get(self, format_id: str) -> FormatSpec:
        if format_id not in self._formats:
            if "concept" in self._formats:
                return self._formats["concept"]
            raise NotFoundError(f"형식 '{format_id}'를 찾을 수 없습니다")
        return self._formats[format_id]

    def list_all(self) -> list[FormatSpec]:
        return list(self._formats.values())

    def list_summaries(self) -> list[FormatSummary]:
        return [
            FormatSummary(
                id=f.id,
                name=f.name,
                name_en=f.name_en,
                description=f.description,
                icon=f.icon,
                section_count_min=f.structure.section_count.min,
                section_count_max=f.structure.section_count.max,
                char_count_standard=f.structure.char_count.standard,
            )
            for f in self._formats.values()
        ]

    def suggest(self, topic: str) -> list[FormatSuggestion]:
        topic_lower = topic.lower()
        scored: list[tuple[float, FormatSpec]] = []

        for spec in self._formats.values():
            hits = sum(1 for s in spec.router_signals if s in topic_lower)
            if hits > 0:
                confidence = min(hits / max(len(spec.router_signals), 1) * 2, 1.0)
                scored.append((confidence, spec))

        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            default = self._formats.get("concept")
            if default:
                scored = [(0.3, default)]

        return [
            FormatSuggestion(
                format_id=spec.id,
                name=spec.name,
                icon=spec.icon,
                confidence=round(conf, 2),
                reason=spec.description,
            )
            for conf, spec in scored[:3]
        ]

    @property
    def format_ids(self) -> list[str]:
        return list(self._formats.keys())


_registry: FormatRegistry | None = None


def get_format_registry() -> FormatRegistry:
    global _registry
    if _registry is None:
        _registry = FormatRegistry()
        _registry.load_all()
    return _registry
