import copy
from unittest.mock import AsyncMock, MagicMock

from app.formats.schema import (
    CharCountSpec,
    ElementSpec,
    FormatSpec,
    RangeSpec,
    SeoSpec,
    StructureSpec,
    ValidationSpec,
)
from app.pipeline.base import StageInput
from app.pipeline.stages.s5_validator import (
    ValidatorStage,
    _check_ai_tell_words,
    _check_burstiness,
    _check_char_count,
    _check_comparison_tables,
    _check_conclusion_section,
    _check_definition_patterns,
    _check_heading_keyword,
    _check_html_tables,
    _check_image_alt,
    _check_intro_section,
    _check_keyword_density,
    _check_keyword_presence,
    _check_no_faq,
    _check_no_references_section,
    _check_quantitative_data,
    _check_readability,
    _check_section_count,
    _check_slop_can_do,
    _check_slop_empty_emphasis,
    _check_slop_monotony,
    _check_slop_superlatives,
    _check_title_length,
    _compute_summary,
    _run_rule_checks,
)

GOOD_CONTENT = (
    "# AI란 무엇인가?\n\n"
    + "## 1. 들어가며\n\n" + "가" * 500 + "\n\n"
    + "## 2. 기본 개념\n\n" + "나" * 800 + "\n\n"
    + "## 3. 활용 사례\n\n" + "다" * 800 + "\n\n"
    + "## 4. 핵심 기술\n\n" + "라" * 800 + "\n\n"
    + "## 5. 도입 방법\n\n" + "마" * 800 + "\n\n"
    + "## 6. 주의사항\n\n" + "바" * 800 + "\n\n"
    + "## 7. 미래 전망\n\n" + "사" * 800 + "\n\n"
    + "## 8. 마치며\n\n" + "아" * 500 + "\n"
)

MOCK_META = {
    "title": "AI란 무엇인가? — 개발자 가이드",
    "seo_keywords": ["AI", "인공지능", "머신러닝"],
}

DEFAULT_SPEC = FormatSpec(
    id="concept",
    name="개념 해설형",
    structure=StructureSpec(
        section_count=RangeSpec(min=7, max=9),
        char_count=CharCountSpec(standard=(6000, 8000), long=(10000, 13000)),
    ),
    elements=ElementSpec(),
    validation=ValidationSpec(
        intro_keywords=["들어가며"],
        closing_keywords=["마치며"],
    ),
    seo=SeoSpec(),
)

MOCK_CLAUDE_VALIDATIONS = {
    "validations": [
        {
            "category": "style",
            "item": "격식체 사용",
            "passed": True,
            "score": 0.95,
            "message": "격식체가 잘 사용됨",
        },
        {
            "category": "aeo",
            "item": "질문-답변 구조",
            "passed": False,
            "score": 0.3,
            "message": "Q&A 구조 부족",
        },
    ]
}


def _make_stage(
    content: str | None = None,
    meta: dict | None = None,
    claude_response: dict | None = None,
    claude_error: Exception | None = None,
) -> tuple[ValidatorStage, AsyncMock, MagicMock]:
    mock_claude = AsyncMock()
    if claude_error:
        mock_claude.run_json.side_effect = claude_error
    else:
        mock_claude.run_json.return_value = (
            claude_response or MOCK_CLAUDE_VALIDATIONS
        )

    mock_fm = MagicMock()

    def read_text_effect(slug: str, filename: str) -> str | None:
        if filename == "final.md":
            return GOOD_CONTENT if content is None else content
        return None

    def read_json_effect(slug: str, filename: str) -> dict | list | None:
        if filename == "meta.json":
            return meta if meta is not None else MOCK_META
        return None

    mock_fm.read_text.side_effect = read_text_effect
    mock_fm.read_json.side_effect = read_json_effect

    return ValidatorStage(mock_claude, mock_fm), mock_claude, mock_fm


def _make_input() -> StageInput:
    return StageInput(
        article_id=1,
        slug="ai란-무엇인가",
        topic="AI란 무엇인가?",
    )


async def test_validator_name() -> None:
    stage, _, _ = _make_stage()
    assert stage.name == "validator"


async def test_validator_success() -> None:
    stage, _, mock_fm = _make_stage()
    result = await stage.execute(_make_input())

    assert result.success is True
    assert result.stage_name == "validator"
    assert "validations" in result.data
    assert "summary" in result.data
    assert result.data["summary"]["total"] > 0

    mock_fm.write_json.assert_called_once()


async def test_validator_no_final_md() -> None:
    stage, _, _ = _make_stage(content=None)
    stage._fm.read_text.side_effect = lambda s, f: None

    result = await stage.execute(_make_input())

    assert result.success is False
    assert "final.md" in result.error


async def test_validator_saves_critique_json() -> None:
    stage, _, mock_fm = _make_stage()
    await stage.execute(_make_input())

    call_args = mock_fm.write_json.call_args[0]
    assert call_args[0] == "ai란-무엇인가"
    assert call_args[1] == "critique.json"
    assert "validations" in call_args[2]
    assert "summary" in call_args[2]


async def test_validator_handles_claude_error() -> None:
    stage, _, _ = _make_stage(claude_error=RuntimeError("CLI fail"))
    result = await stage.execute(_make_input())

    assert result.success is True
    assert result.data["summary"]["total"] == 22


async def test_validator_combines_rule_and_claude() -> None:
    stage, _, _ = _make_stage()
    result = await stage.execute(_make_input())

    assert result.data["summary"]["total"] == 24


def test_check_char_count_pass() -> None:
    result = _check_char_count("가" * 7000, DEFAULT_SPEC)
    assert result["passed"] is True


def test_check_char_count_too_short() -> None:
    result = _check_char_count("가" * 100, DEFAULT_SPEC)
    assert result["passed"] is False


def test_check_char_count_too_long() -> None:
    result = _check_char_count("가" * 20000, DEFAULT_SPEC)
    assert result["passed"] is False


def test_check_section_count_pass() -> None:
    content = "\n".join(f"## Section {i}" for i in range(8))
    result = _check_section_count(content, DEFAULT_SPEC)
    assert result["passed"] is True


def test_check_section_count_too_few() -> None:
    content = "## Section 1\n## Section 2"
    result = _check_section_count(content, DEFAULT_SPEC)
    assert result["passed"] is False


def test_check_intro_section() -> None:
    assert _check_intro_section("## 1. 들어가며\n본문", DEFAULT_SPEC)["passed"] is True
    assert _check_intro_section("## 1. 소개\n본문", DEFAULT_SPEC)["passed"] is False


def test_check_conclusion_section() -> None:
    assert _check_conclusion_section("## 마치며\n결론", DEFAULT_SPEC)["passed"] is True
    assert _check_conclusion_section("## 결론\n끝", DEFAULT_SPEC)["passed"] is False


def test_check_no_faq_pass() -> None:
    assert _check_no_faq("일반 본문입니다.")["passed"] is True


def test_check_no_faq_fail() -> None:
    assert _check_no_faq("## FAQ\n질문1")["passed"] is False
    assert _check_no_faq("자주 묻는 질문")["passed"] is False


def test_check_no_references_section() -> None:
    assert _check_no_references_section("일반 본문")["passed"] is True
    assert _check_no_references_section("## 참고 자료\n링크")["passed"] is False
    assert _check_no_references_section("## References\nlinks")["passed"] is False


def test_check_html_tables_pass() -> None:
    assert _check_html_tables("본문 <table><tr><td>값</td></tr></table>")["passed"] is True


def test_check_html_tables_fail() -> None:
    content = "| 항목 | 값 |\n|---|---|\n| A | 1 |"
    assert _check_html_tables(content)["passed"] is False


def test_check_html_tables_in_code_block_pass() -> None:
    content = "```\n| 항목 | 값 |\n|---|---|\n```"
    assert _check_html_tables(content)["passed"] is True


def test_check_title_length_pass() -> None:
    assert _check_title_length({"title": "짧은 제목"})["passed"] is True


def test_check_title_length_fail() -> None:
    assert _check_title_length({"title": "가" * 70})["passed"] is False


def test_check_title_length_empty() -> None:
    assert _check_title_length({})["passed"] is False


def test_check_keyword_presence() -> None:
    content = "AI와 인공지능에 대해 알아봅니다."
    meta = {"seo_keywords": ["AI", "인공지능", "딥러닝"]}
    result = _check_keyword_presence(content, meta)
    assert result["passed"] is True
    assert result["score"] > 0.5


def test_check_keyword_no_keywords() -> None:
    result = _check_keyword_presence("본문", {})
    assert result["passed"] is False


def test_compute_summary() -> None:
    validations = [
        {"category": "style", "passed": True},
        {"category": "style", "passed": False},
        {"category": "seo", "passed": True},
    ]
    summary = _compute_summary(validations)
    assert summary["total"] == 3
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert summary["by_category"]["style"]["total"] == 2
    assert summary["by_category"]["style"]["passed"] == 1


def test_compute_summary_empty() -> None:
    summary = _compute_summary([])
    assert summary["total"] == 0
    assert summary["score"] == 0.0


def test_run_rule_checks_returns_twenty_two() -> None:
    results = _run_rule_checks(GOOD_CONTENT, MOCK_META, DEFAULT_SPEC)
    assert len(results) == 22


def test_slop_can_do_pass() -> None:
    assert _check_slop_can_do("일반 문장입니다.")["passed"] is True


def test_slop_can_do_fail() -> None:
    text = "할 수 있습니다. " * 8
    result = _check_slop_can_do(text)
    assert result["passed"] is False
    assert result["score"] < 1.0


def test_slop_empty_emphasis_pass() -> None:
    assert _check_slop_empty_emphasis("이것은 중요한 개념입니다.")["passed"] is True


def test_slop_empty_emphasis_fail() -> None:
    text = "매우 중요합니다. 핵심적입니다. 가장 중요한 것은 매우 핵심입니다."
    assert _check_slop_empty_emphasis(text)["passed"] is False


def test_slop_monotony_pass() -> None:
    text = "A는 B입니다. C를 합시다. D가 됩니다."
    assert _check_slop_monotony(text)["passed"] is True


def test_slop_monotony_fail() -> None:
    text = "A입니다. B입니다. C입니다. D입니다. E입니다."
    assert _check_slop_monotony(text)["passed"] is False


def test_slop_superlatives_pass() -> None:
    assert _check_slop_superlatives("좋은 도구입니다.")["passed"] is True


def test_slop_superlatives_fail() -> None:
    text = "최고의 도구이자 유일한 방법이며 가장 좋은 선택입니다."
    assert _check_slop_superlatives(text)["passed"] is False


def test_readability_normal() -> None:
    text = "트랜스포머 아키텍처는 자연어 처리의 핵심 기술입니다. 이 모델은 어텐션 메커니즘을 활용하여 긴 문맥을 효과적으로 처리합니다. 특히 셀프 어텐션은 입력 시퀀스 내의 모든 위치 간 관계를 동시에 계산합니다."
    result = _check_readability(text)
    assert result["passed"] is True


def test_readability_too_long() -> None:
    text = ("가" * 100 + ". ") * 5
    result = _check_readability(text)
    assert result["passed"] is False


# ──────────────────────────────────────────────
# Oracle 통합 테스트
# ──────────────────────────────────────────────

_MOCK_ORACLE_VALIDATIONS_TEMPLATE = {
    "validations": [
        {
            "category": "style",
            "item": "비유 적절성",
            "passed": True,
            "score": 0.85,
            "message": "비유가 적절함",
        },
        {
            "category": "aeo",
            "item": "정의 품질",
            "passed": False,
            "score": 0.5,
            "message": "정의가 모호함",
        },
    ]
}


def _fresh_oracle_response() -> dict:
    """_run_oracle이 딕셔너리를 mutation하므로 매 호출마다 새 복사본을 반환한다."""
    return copy.deepcopy(_MOCK_ORACLE_VALIDATIONS_TEMPLATE)


def _make_input_with_oracle() -> StageInput:
    return StageInput(
        article_id=1,
        slug="ai란-무엇인가",
        topic="AI란 무엇인가?",
        data={"use_oracle": True},
    )


async def test_validator_calls_oracle_when_use_oracle_flag() -> None:
    """use_oracle=True 플래그가 있으면 oracle이 호출되어 run_json이 2번 호출된다."""
    stage, mock_claude, _ = _make_stage()
    mock_claude.run_json.side_effect = [
        MOCK_CLAUDE_VALIDATIONS,
        _fresh_oracle_response(),
    ]

    result = await stage.execute(_make_input_with_oracle())

    assert result.success is True
    assert mock_claude.run_json.call_count == 2
    assert result.data["oracle_used"] is True


async def test_validator_calls_oracle_for_long_content() -> None:
    """content가 10000자 이상이면 use_oracle 플래그 없이도 oracle이 호출된다."""
    long_content = "가" * 10001
    stage, mock_claude, _ = _make_stage(content=long_content)
    mock_claude.run_json.side_effect = [
        MOCK_CLAUDE_VALIDATIONS,
        _fresh_oracle_response(),
    ]

    result = await stage.execute(_make_input())

    assert result.success is True
    assert mock_claude.run_json.call_count == 2
    assert result.data["oracle_used"] is True


async def test_validator_oracle_items_prefixed() -> None:
    """Oracle 검증 항목에는 '[Oracle]' 접두사가 붙는다."""
    stage, mock_claude, _ = _make_stage()
    mock_claude.run_json.side_effect = [
        MOCK_CLAUDE_VALIDATIONS,
        _fresh_oracle_response(),
    ]

    result = await stage.execute(_make_input_with_oracle())

    oracle_items = [
        v for v in result.data["validations"]
        if v.get("item", "").startswith("[Oracle]")
    ]
    assert len(oracle_items) == 2
    assert oracle_items[0]["item"] == "[Oracle] 비유 적절성"
    assert oracle_items[1]["item"] == "[Oracle] 정의 품질"


async def test_validator_oracle_failure_returns_empty() -> None:
    """Oracle Claude 호출이 실패해도 전체 결과는 성공하며, rule+validator 항목만 남는다."""
    stage, mock_claude, _ = _make_stage()
    mock_claude.run_json.side_effect = [
        MOCK_CLAUDE_VALIDATIONS,
        RuntimeError("Oracle CLI fail"),
    ]

    result = await stage.execute(_make_input_with_oracle())

    assert result.success is True
    assert result.data["oracle_used"] is True
    # rule 22개 + claude validator 2개 = 24개 (oracle 실패로 0개 추가)
    assert result.data["summary"]["total"] == 24
    oracle_items = [
        v for v in result.data["validations"]
        if v.get("item", "").startswith("[Oracle]")
    ]
    assert len(oracle_items) == 0


async def test_validator_no_oracle_by_default() -> None:
    """기본 StageInput(use_oracle 없음, 짧은 content)에서는 oracle이 호출되지 않는다."""
    stage, mock_claude, _ = _make_stage()

    result = await stage.execute(_make_input())

    assert result.success is True
    assert mock_claude.run_json.call_count == 1
    assert result.data["oracle_used"] is False


# ──────────────────────────────────────────────
# Phase 2: 신규 검증 항목 테스트 (SEO/AEO/GEO + AI감지)
# ──────────────────────────────────────────────


def test_keyword_density_pass() -> None:
    content = "AI는 중요한 기술입니다. " * 30 + "가" * 3000
    meta = {"seo_keywords": ["AI"]}
    result = _check_keyword_density(content, meta)
    assert result["passed"] is True
    assert result["category"] == "seo"


def test_keyword_density_too_high() -> None:
    content = "AI " * 500
    meta = {"seo_keywords": ["AI"]}
    result = _check_keyword_density(content, meta)
    assert result["passed"] is False


def test_keyword_density_no_keywords() -> None:
    result = _check_keyword_density("본문입니다.", {})
    assert result["passed"] is False


def test_heading_keyword_pass() -> None:
    content = "## AI의 개념\n## AI 활용 사례\n## 결론"
    meta = {"seo_keywords": ["AI"]}
    result = _check_heading_keyword(content, meta)
    assert result["passed"] is True


def test_heading_keyword_fail() -> None:
    content = "## 들어가며\n## 마치며\n## 기타"
    meta = {"seo_keywords": ["AI", "인공지능"]}
    result = _check_heading_keyword(content, meta)
    assert result["passed"] is False


def test_image_alt_pass() -> None:
    content = "![AI 아키텍처](img.png)\n![모델 구조](model.png)"
    result = _check_image_alt(content)
    assert result["passed"] is True


def test_image_alt_fail() -> None:
    content = "![](img.png)\n![AI 구조](model.png)"
    result = _check_image_alt(content)
    assert result["passed"] is False


def test_image_alt_no_images() -> None:
    result = _check_image_alt("이미지 없는 본문입니다.")
    assert result["passed"] is True


def test_definition_patterns_pass() -> None:
    content = "AI란 인공지능을 의미합니다. 즉, 기계가 학습하는 것이다."
    result = _check_definition_patterns(content)
    assert result["passed"] is True


def test_definition_patterns_fail() -> None:
    content = "좋은 기술이 있습니다. 사용해 봅시다."
    result = _check_definition_patterns(content)
    assert result["passed"] is False


def test_comparison_tables_pass() -> None:
    content = "비교 분석입니다. <table><tr><td>A</td></tr></table>"
    result = _check_comparison_tables(content)
    assert result["passed"] is True


def test_comparison_tables_fail() -> None:
    content = "A vs B 비교입니다. 차이점은 명확합니다. 장단점을 살펴봅시다."
    result = _check_comparison_tables(content)
    assert result["passed"] is False


def test_quantitative_data_pass() -> None:
    content = "처리 속도 30% 향상. 메모리 2GB 사용. 응답 시간 50ms."
    result = _check_quantitative_data(content)
    assert result["passed"] is True


def test_quantitative_data_fail() -> None:
    content = "좋은 성능을 보여줍니다. 빠릅니다."
    result = _check_quantitative_data(content)
    assert result["passed"] is False


def test_ai_tell_words_pass() -> None:
    result = _check_ai_tell_words("일반적인 기술 문서입니다.")
    assert result["passed"] is True


def test_ai_tell_words_fail() -> None:
    text = (
        "살펴보겠습니다. 알아보겠습니다. 확인해 보겠습니다. "
        "다루어 보겠습니다. 알아보도록 하겠습니다."
    )
    result = _check_ai_tell_words(text)
    assert result["passed"] is False


def test_burstiness_pass() -> None:
    text = "짧다. 이것은 아주 긴 문장으로 다양한 내용을 포함하고 있습니다. 중간. 또 다른 긴 문장이 여기 있다. 끝."
    result = _check_burstiness(text)
    assert result["category"] == "geo"


def test_burstiness_uniform_fail() -> None:
    text = ". ".join(["동일길이문장" * 3] * 10) + "."
    result = _check_burstiness(text)
    assert result["category"] == "geo"
