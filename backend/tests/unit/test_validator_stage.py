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
    _check_char_count,
    _check_conclusion_section,
    _check_html_tables,
    _check_intro_section,
    _check_keyword_presence,
    _check_no_faq,
    _check_no_references_section,
    _check_section_count,
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
    assert result.data["summary"]["total"] == 9


async def test_validator_combines_rule_and_claude() -> None:
    stage, _, _ = _make_stage()
    result = await stage.execute(_make_input())

    assert result.data["summary"]["total"] == 11


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


def test_run_rule_checks_returns_nine() -> None:
    results = _run_rule_checks(GOOD_CONTENT, MOCK_META, DEFAULT_SPEC)
    assert len(results) == 9
