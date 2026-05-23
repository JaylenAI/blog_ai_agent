from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from app.exceptions import NotFoundError
from app.formats.registry import FormatRegistry, get_format_registry
from app.formats.schema import (
    CharCountSpec,
    FormatSpec,
    FormatSuggestion,
    FormatSummary,
    RangeSpec,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# FormatSpec / schema validation
# ---------------------------------------------------------------------------


class TestFormatSpecValidation:
    """FormatSpec Pydantic 모델의 필수 필드 및 기본값 검증."""

    def test_minimal_spec_requires_id_and_name(self) -> None:
        spec = FormatSpec(id="test", name="테스트")
        assert spec.id == "test"
        assert spec.name == "테스트"
        assert spec.name_en == ""
        assert spec.description == ""
        assert spec.icon == ""
        assert spec.router_signals == []

    def test_missing_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            FormatSpec(name="이름만")  # type: ignore[call-arg]

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            FormatSpec(id="only-id")  # type: ignore[call-arg]

    def test_structure_defaults(self) -> None:
        spec = FormatSpec(id="t", name="n")
        assert spec.structure.section_count.min == 7
        assert spec.structure.section_count.max == 9
        assert spec.structure.char_count.standard == (6000, 8000)
        assert spec.structure.required_sections == []
        assert spec.structure.optional_sections == []

    def test_elements_defaults(self) -> None:
        spec = FormatSpec(id="t", name="n")
        assert spec.elements.tables_min == 1
        assert spec.elements.use_metaphors is False
        assert spec.elements.use_callout_boxes is True
        assert spec.elements.diagram_types == []

    def test_validation_defaults(self) -> None:
        spec = FormatSpec(id="t", name="n")
        assert spec.validation.intro_keywords == ["들어가며"]
        assert spec.validation.closing_keywords == ["마치며"]
        assert "FAQ" in spec.validation.forbidden_sections

    def test_seo_defaults(self) -> None:
        spec = FormatSpec(id="t", name="n")
        assert spec.seo.title_max_chars == 60
        assert spec.seo.tags_count == 10
        assert spec.seo.title_patterns == []

    def test_full_spec_from_dict(self) -> None:
        data = {
            "id": "full",
            "name": "풀 스펙",
            "name_en": "Full Spec",
            "description": "모든 필드",
            "icon": "🔥",
            "structure": {
                "intro_style": "직설적",
                "closing_style": "요약",
                "required_sections": ["들어가며", "마치며"],
                "optional_sections": ["부록"],
                "section_count": {"min": 5, "max": 7},
                "char_count": {"standard": [3000, 5000], "long": [8000, 10000]},
            },
            "elements": {
                "tables_min": 2,
                "code_blocks": [1, 3],
                "diagram_types": ["flow"],
                "expected_images": [0, 1],
                "use_metaphors": True,
                "use_callout_boxes": False,
            },
            "validation": {
                "intro_keywords": ["시작"],
                "closing_keywords": ["끝"],
                "forbidden_sections": ["참고"],
            },
            "seo": {
                "title_max_chars": 50,
                "tags_count": 5,
                "title_patterns": ["{t} 정리"],
            },
            "prompt_instructions": "상세 지침",
            "router_signals": ["키워드A", "키워드B"],
        }
        spec = FormatSpec(**data)
        assert spec.structure.intro_style == "직설적"
        assert spec.elements.use_callout_boxes is False
        assert spec.seo.title_max_chars == 50
        assert len(spec.router_signals) == 2


class TestSubSchemas:
    """하위 스키마 모델 개별 검증."""

    def test_range_spec_defaults(self) -> None:
        r = RangeSpec()
        assert r.min == 0
        assert r.max == 99

    def test_char_count_spec_defaults(self) -> None:
        c = CharCountSpec()
        assert c.standard == (6000, 8000)
        assert c.long == (10000, 13000)

    def test_format_summary_fields(self) -> None:
        s = FormatSummary(
            id="x",
            name="X",
            name_en="EX",
            description="d",
            icon="i",
            section_count_min=3,
            section_count_max=5,
            char_count_standard=(1000, 2000),
        )
        assert s.id == "x"
        assert s.char_count_standard == (1000, 2000)

    def test_format_suggestion_fields(self) -> None:
        s = FormatSuggestion(
            format_id="y",
            name="Y",
            icon="i",
            confidence=0.75,
            reason="이유",
        )
        assert s.confidence == 0.75


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


class TestFormatRegistryLoad:
    def test_loads_all_yaml_files(self, registry: FormatRegistry) -> None:
        assert len(registry.format_ids) == 2
        assert "concept" in registry.format_ids
        assert "tutorial" in registry.format_ids

    def test_ignores_invalid_yaml(self, tmp_defs: Path) -> None:
        (tmp_defs / "broken.yaml").write_text(
            "not: [valid: yaml: {", encoding="utf-8"
        )
        reg = FormatRegistry()
        reg.load_all(tmp_defs)
        # broken.yaml 실패해도 나머지 2개는 정상 로딩
        assert len(reg.format_ids) == 2

    def test_skips_non_dict_yaml(self, tmp_defs: Path) -> None:
        """YAML 파일 내용이 dict가 아닌 경우 (예: 리스트) 스킵."""
        (tmp_defs / "list.yaml").write_text("- item1\n- item2\n", encoding="utf-8")
        reg = FormatRegistry()
        reg.load_all(tmp_defs)
        assert len(reg.format_ids) == 2

    def test_skips_yaml_with_missing_required_fields(self, tmp_defs: Path) -> None:
        """id/name 누락 등 FormatSpec 검증 실패 시 해당 파일만 스킵."""
        (tmp_defs / "bad_spec.yaml").write_text(
            yaml.dump({"description": "이름 없음"}, allow_unicode=True),
            encoding="utf-8",
        )
        reg = FormatRegistry()
        reg.load_all(tmp_defs)
        assert len(reg.format_ids) == 2
        assert "bad_spec" not in reg.format_ids

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

    def test_load_all_clears_previous(self, tmp_defs: Path, tmp_path: Path) -> None:
        """load_all 재호출 시 이전 데이터가 초기화되는지 확인."""
        reg = FormatRegistry()
        reg.load_all(tmp_defs)
        assert len(reg.format_ids) == 2

        empty = tmp_path / "empty2"
        empty.mkdir()
        reg.load_all(empty)
        assert len(reg.format_ids) == 0

    def test_only_reads_yaml_extension(self, tmp_defs: Path) -> None:
        """*.yaml이 아닌 파일은 무시."""
        (tmp_defs / "readme.md").write_text("# README", encoding="utf-8")
        (tmp_defs / "data.json").write_text('{"id": "json"}', encoding="utf-8")
        reg = FormatRegistry()
        reg.load_all(tmp_defs)
        assert len(reg.format_ids) == 2

    def test_loads_sorted_by_filename(self, tmp_defs: Path) -> None:
        """파일명 정렬 순서대로 로딩 (같은 id면 마지막 우선)."""
        reg = FormatRegistry()
        reg.load_all(tmp_defs)
        # concept.yaml < tutorial.yaml 이므로 concept이 먼저 로딩됨
        assert registry_ids_in_insertion_order(reg) == ["concept", "tutorial"]


def registry_ids_in_insertion_order(reg: FormatRegistry) -> list[str]:
    """dict 삽입 순서 기반으로 format_ids 반환."""
    return reg.format_ids


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


class TestFormatRegistryGet:
    def test_get_existing(self, registry: FormatRegistry) -> None:
        spec = registry.get("concept")
        assert spec.id == "concept"
        assert spec.name == "개념 해설형"

    def test_get_returns_correct_spec_fields(self, registry: FormatRegistry) -> None:
        spec = registry.get("tutorial")
        assert spec.id == "tutorial"
        assert spec.name_en == "Tutorial"
        assert spec.description == "단계별 실습 가이드"
        assert spec.icon == "📝"
        assert spec.structure.section_count.min == 7
        assert spec.structure.section_count.max == 10
        assert spec.elements.code_blocks == (8, 20)
        assert spec.elements.use_metaphors is False
        assert "구축" in spec.router_signals

    def test_get_unknown_falls_back_to_concept(
        self, registry: FormatRegistry
    ) -> None:
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
        (defs / "other.yaml").write_text(
            yaml.dump(data, allow_unicode=True), encoding="utf-8"
        )

        reg = FormatRegistry()
        reg.load_all(defs)
        with pytest.raises(NotFoundError):
            reg.get("nonexistent")

    def test_get_empty_string_id_falls_back(self, registry: FormatRegistry) -> None:
        """빈 문자열 ID도 fallback 동작."""
        spec = registry.get("")
        assert spec.id == "concept"


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


class TestFormatRegistryList:
    def test_list_all(self, registry: FormatRegistry) -> None:
        all_formats = registry.list_all()
        assert len(all_formats) == 2
        assert all(isinstance(f, FormatSpec) for f in all_formats)

    def test_list_all_returns_new_list(self, registry: FormatRegistry) -> None:
        """반환 리스트 변경이 내부 상태에 영향 없음."""
        a = registry.list_all()
        a.clear()
        assert len(registry.list_all()) == 2

    def test_list_summaries(self, registry: FormatRegistry) -> None:
        summaries = registry.list_summaries()
        assert len(summaries) == 2
        s = next(s for s in summaries if s.id == "concept")
        assert s.section_count_min == 7
        assert s.section_count_max == 9
        assert s.char_count_standard == (6000, 8000)

    def test_list_summaries_contains_all_fields(
        self, registry: FormatRegistry
    ) -> None:
        summaries = registry.list_summaries()
        for s in summaries:
            assert isinstance(s, FormatSummary)
            assert s.id
            assert s.name
            assert s.name_en
            assert s.description
            assert s.icon

    def test_list_all_empty_registry(self) -> None:
        reg = FormatRegistry()
        assert reg.list_all() == []

    def test_list_summaries_empty_registry(self) -> None:
        reg = FormatRegistry()
        assert reg.list_summaries() == []

    def test_format_ids_property(self, registry: FormatRegistry) -> None:
        ids = registry.format_ids
        assert isinstance(ids, list)
        assert set(ids) == {"concept", "tutorial"}


# ---------------------------------------------------------------------------
# Suggest
# ---------------------------------------------------------------------------


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

    def test_suggest_returns_max_3(self, tmp_path: Path) -> None:
        """4개 이상의 형식이 매칭되어도 최대 3개만 반환."""
        defs = tmp_path / "many"
        defs.mkdir()
        for i in range(5):
            data = {
                "id": f"fmt{i}",
                "name": f"형식{i}",
                "router_signals": ["공통키워드"],
            }
            (defs / f"fmt{i}.yaml").write_text(
                yaml.dump(data, allow_unicode=True), encoding="utf-8"
            )
        reg = FormatRegistry()
        reg.load_all(defs)
        results = reg.suggest("공통키워드")
        assert len(results) <= 3

    def test_suggest_returns_format_suggestion_type(
        self, registry: FormatRegistry
    ) -> None:
        results = registry.suggest("구축")
        for r in results:
            assert isinstance(r, FormatSuggestion)
            assert r.format_id
            assert r.name
            assert isinstance(r.confidence, float)

    def test_suggest_case_insensitive(self, tmp_path: Path) -> None:
        """토픽 소문자 변환 후 매칭하므로 대소문자 무관."""
        defs = tmp_path / "case"
        defs.mkdir()
        data = {
            "id": "eng",
            "name": "영문형",
            "router_signals": ["docker", "kubernetes"],
        }
        (defs / "eng.yaml").write_text(
            yaml.dump(data, allow_unicode=True), encoding="utf-8"
        )
        reg = FormatRegistry()
        reg.load_all(defs)
        results = reg.suggest("Docker와 Kubernetes 비교")
        assert len(results) > 0
        assert results[0].format_id == "eng"

    def test_suggest_empty_topic_returns_default(
        self, registry: FormatRegistry
    ) -> None:
        results = registry.suggest("")
        # 빈 문자열에서는 아무 signal도 매칭 안 됨 -> concept default
        assert len(results) == 1
        assert results[0].format_id == "concept"

    def test_suggest_no_concept_no_match_returns_empty(
        self, tmp_path: Path
    ) -> None:
        """concept 형식이 없고 매칭도 없으면 빈 리스트 반환."""
        defs = tmp_path / "no_concept"
        defs.mkdir()
        data = {
            "id": "niche",
            "name": "특수형",
            "router_signals": ["매우특수한단어"],
        }
        (defs / "niche.yaml").write_text(
            yaml.dump(data, allow_unicode=True), encoding="utf-8"
        )
        reg = FormatRegistry()
        reg.load_all(defs)
        results = reg.suggest("전혀 관련 없는 주제")
        assert results == []


# ---------------------------------------------------------------------------
# Singleton (get_format_registry)
# ---------------------------------------------------------------------------


class TestGetFormatRegistry:
    def test_returns_registry_instance(self) -> None:
        with patch("app.formats.registry._registry", None):
            reg = get_format_registry()
            assert isinstance(reg, FormatRegistry)

    def test_singleton_returns_same_instance(self) -> None:
        with patch("app.formats.registry._registry", None):
            reg1 = get_format_registry()
            reg2 = get_format_registry()
            assert reg1 is reg2

    def test_loads_real_definitions(self) -> None:
        """실제 definitions 디렉토리에서 YAML 파일을 로드하는지 확인."""
        with patch("app.formats.registry._registry", None):
            reg = get_format_registry()
            assert len(reg.format_ids) > 0
            assert "concept" in reg.format_ids
