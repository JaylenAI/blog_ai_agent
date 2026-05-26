from app.claude.prompts.oracle import ORACLE_CRITERIA, OraclePrompt


def test_oracle_prompt_renders_with_content() -> None:
    prompt = OraclePrompt()
    output = prompt.render(content="블로그 본문 테스트 내용입니다.")

    assert "블로그 본문 테스트 내용입니다." in output


def test_oracle_prompt_renders_with_keywords() -> None:
    prompt = OraclePrompt()
    output = prompt.render(content="본문", seo_keywords="AI, 머신러닝, 딥러닝")

    assert "AI, 머신러닝, 딥러닝" in output


def test_oracle_prompt_renders_without_keywords_shows_default() -> None:
    prompt = OraclePrompt()
    output = prompt.render(content="본문")

    assert "없음" in output


def test_oracle_prompt_includes_all_criteria() -> None:
    prompt = OraclePrompt()
    output = prompt.render(content="본문")

    for _cat, name, _desc in ORACLE_CRITERIA:
        assert name in output, f"기준 '{name}'이 프롬프트 출력에 포함되지 않음"


def test_oracle_prompt_has_json_format() -> None:
    prompt = OraclePrompt()
    output = prompt.render(content="본문")

    assert "[OUTPUT FORMAT]" in output
    assert '"validations"' in output
    assert '"category"' in output
    assert '"passed"' in output
    assert '"score"' in output


def test_oracle_criteria_has_five_items() -> None:
    assert len(ORACLE_CRITERIA) == 5


def test_oracle_criteria_tuple_structure() -> None:
    for item in ORACLE_CRITERIA:
        assert len(item) == 3
        cat, name, desc = item
        assert isinstance(cat, str)
        assert isinstance(name, str)
        assert isinstance(desc, str)
        assert cat in ("style", "aeo", "geo")
