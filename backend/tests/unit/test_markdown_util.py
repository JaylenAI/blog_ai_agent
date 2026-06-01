from app.utils.markdown import strip_wrapping_code_fence


def test_strips_markdown_wrapping_fence() -> None:
    text = "```markdown\n## 제목\n\n본문입니다.\n```"
    assert strip_wrapping_code_fence(text) == "## 제목\n\n본문입니다."


def test_strips_bare_wrapping_fence() -> None:
    text = "```\n## 제목\n본문\n```"
    assert strip_wrapping_code_fence(text) == "## 제목\n본문"


def test_keeps_inner_code_blocks() -> None:
    """바깥 펜스를 벗기되 본문 안의 정상 코드블록은 유지한다."""
    text = "```markdown\n## 제목\n\n```bash\nls -l\n```\n\n끝.\n```"
    result = strip_wrapping_code_fence(text)
    assert result.startswith("## 제목")
    assert "```bash\nls -l\n```" in result
    assert not result.startswith("```markdown")


def test_does_not_touch_real_code_block() -> None:
    """언어가 bash 등이면 진짜 코드블록이므로 벗기지 않는다."""
    text = "```bash\nls -l\n```"
    assert strip_wrapping_code_fence(text) == text


def test_no_fence_returns_unchanged() -> None:
    text = "## 제목\n\n그냥 본문입니다."
    assert strip_wrapping_code_fence(text) == text


def test_double_wrapping_is_unwrapped() -> None:
    text = "```markdown\n```markdown\n## 제목\n```\n```"
    result = strip_wrapping_code_fence(text)
    assert result == "## 제목"


def test_partial_fence_not_wrapping_is_kept() -> None:
    """본문 일부만 펜스인 경우(전체를 감싸지 않음)는 그대로 둔다."""
    text = "앞 문단\n\n```bash\nls\n```\n\n뒤 문단"
    assert strip_wrapping_code_fence(text) == text
