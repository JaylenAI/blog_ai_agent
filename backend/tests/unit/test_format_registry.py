from pathlib import Path
from textwrap import dedent

import pytest
import yaml

from app.formats.registry import FormatRegistry
from app.formats.schema import FormatSpec


@pytest.fixture
def tmp_defs(tmp_path: Path) -> Path:
    defs_dir = tmp_path / "definitions"
    defs_dir.mkdir()

    concept = {
        "id": "concept",
        "name": "개념 해설형",
        "name_en": "Concept Explainer",
        "description": "기술 개념을 비유와 함께 설명",
        "icon": "📘",
        "structure": {
            "section_count": {"min": 7, "max": 9},
            "char_count": {"standard": [6000, 8000], "long": [10000, 13000]},
        },
        "elements": {
            "tables_min": 1,
            "code_blocks": [2, 8],
            "expected_images": [1, 3],
            "use_metaphors": True,
        },
        "validation": {
            "intro_keywords": ["들어가며"],
            "closing_keywords": ["마치며"],
        },
        "seo": {"title_patterns": ["{topic} 완벽 가이드"]},
        "prompt_instructions": "비유를 활용하세요",
        "router_signals": ["개념", "이해", "가이드", "완벽"],
    }
    (defs_dir / "concept.yaml").write_text(
        yaml.dump(concept, allow_unicode=True), encoding="utf-8"
    )

    tutorial = {
        "id": "tutorial",
        "name": "실습 튜토리얼형",
        "name_en": "Tutorial",
        "description": "단계별 실습 가이드",
        "icon": "📝",
        "structure": {
            "section_count": {"min": 7, "max": 10},
            "char_count": {"standard": [7000, 10000], "long": [12000, 15000]},
        },
        "elements": {
            "tables_min": 0,
            "code_blocks": [8, 20],
            "expected_images": [0, 2],
            "use_metaphors": False,
        },
        "validation": {
            "intro_keywords": ["시작하기", "들어가며"],
            "closing_keywords": ["마치며", "정리"],
        },
        "seo": {"title_patterns": ["{topic} 구축하기"]},
        "prompt_instructions": "실습 단계를 명확히",
        "router_signals": ["구축", "만들기", "설치", "따라하기", "실습"],
    }
    (defs_dir / "tutorial.yaml").write_text(
        yaml.dump(tutorial, allow_unicode=True), encoding="utf-8"
    )

    return defs_dir


@pytest.fixture
def registry(tmp_defs: Path) -> FormatRegistry:
    reg = FormatRegistry()
    reg.load_all(tmp_defs)
    return reg


class TestFormatRegistryLoad:
    def test_loads_all_yaml_files(self, registry: FormatRegistry) -> None:
        assert len(registry.format_ids) == 2
        assert "concept" in registry.format_ids
        assert "tutorial" in registry.format_ids

    def test_ignores_invalid_yaml(self, tmp_defs: Path) -> None:
        (tmp_defs / "broken.yaml").write_text("not: [valid: yaml: {", encoding="utf-8")
        reg = FormatRegistry()
        reg.load_all(tmp_defs)
        assert len(reg.format_ids) == 2

    def test_empty_dir(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        reg = FormatRegistry()
        reg.load_all(empty)
        assert len(reg.format_ids) == 0

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        reg = FormatRegistry()
        reg.load_all(tmp_path / "nonexistent")
        assert len(reg.format_ids) == 0


class TestFormatRegistryGet:
    def test_get_existing(self, registry: FormatRegistry) -> None:
        spec = registry.get("concept")
        assert spec.id == "concept"
        assert spec.name == "개념 해설형"

    def test_get_unknown_falls_back_to_concept(self, registry: FormatRegistry) -> None:
        spec = registry.get("nonexistent")
        assert spec.id == "concept"

    def test_get_unknown_without_concept_raises(self, tmp_path: Path) -> None:
        defs = tmp_path / "defs"
        defs.mkdir()
        data = {
            "id": "other",
            "name": "기타",
            "structure": {
                "section_count": {"min": 3, "max": 5},
                "char_count": {"standard": [1000, 2000]},
            },
            "elements": {
                "tables_min": 0,
                "code_blocks": [0, 1],
                "expected_images": [0, 1],
            },
            "validation": {},
            "seo": {},
        }
        (defs / "other.yaml").write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")

        reg = FormatRegistry()
        reg.load_all(defs)
        with pytest.raises(KeyError):
            reg.get("nonexistent")


class TestFormatRegistryList:
    def test_list_all(self, registry: FormatRegistry) -> None:
        all_formats = registry.list_all()
        assert len(all_formats) == 2
        assert all(isinstance(f, FormatSpec) for f in all_formats)

    def test_list_summaries(self, registry: FormatRegistry) -> None:
        summaries = registry.list_summaries()
        assert len(summaries) == 2
        s = next(s for s in summaries if s.id == "concept")
        assert s.section_count_min == 7
        assert s.section_count_max == 9
        assert s.char_count_standard == (6000, 8000)


class TestFormatRegistrySuggest:
    def test_suggest_matches_signals(self, registry: FormatRegistry) -> None:
        results = registry.suggest("MCP 서버 구축하기 실습")
        assert len(results) > 0
        assert results[0].format_id == "tutorial"

    def test_suggest_no_match_returns_concept_default(
        self, registry: FormatRegistry
    ) -> None:
        results = registry.suggest("아무 관련 없는 주제")
        assert len(results) == 1
        assert results[0].format_id == "concept"
        assert results[0].confidence == 0.3

    def test_suggest_multiple_matches_sorted_by_confidence(
        self, registry: FormatRegistry
    ) -> None:
        results = registry.suggest("완벽 가이드로 이해하며 구축하기")
        assert len(results) >= 2
        assert results[0].confidence >= results[1].confidence

    def test_suggest_confidence_capped_at_1(self, registry: FormatRegistry) -> None:
        results = registry.suggest("구축 만들기 설치 따라하기 실습")
        for r in results:
            assert r.confidence <= 1.0
