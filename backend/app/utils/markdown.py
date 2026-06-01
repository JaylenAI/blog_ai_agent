from __future__ import annotations

import re

# 본문 전체를 감싼 코드펜스를 탐지한다. LLM이 마크다운 결과물을
# ```markdown ... ``` 또는 ``` ... ``` 으로 한 번 더 감싸는 실수를 교정한다.
_WRAPPING_FENCE = re.compile(
    r"^\s*```[ \t]*([A-Za-z0-9_-]*)[ \t]*\r?\n(.*?)\r?\n```[ \t]*\s*$",
    re.DOTALL,
)

# 코드펜스로 인정하지 않을 언어 토큰 — 이 경우는 진짜 코드블록일 수 있으므로 벗기지 않는다.
_FENCE_LANGS_TO_STRIP = {"", "markdown", "md", "mdx"}


def strip_wrapping_code_fence(text: str) -> str:
    """본문 전체를 감싼 불필요한 코드펜스를 제거한다.

    LLM이 글 전체를 ```markdown ... ``` 으로 감싸 반환하면 렌더러가
    글 전체를 하나의 코드블록으로 표시한다. 바깥 펜스가 본문을 통째로
    감싸고 있을 때만 제거하며, 본문 중간의 정상 코드블록(```bash 등)은
    건드리지 않는다.
    """
    if "```" not in text:
        return text

    match = _WRAPPING_FENCE.match(text.strip())
    if match is None:
        return text

    lang = match.group(1).lower()
    if lang not in _FENCE_LANGS_TO_STRIP:
        return text

    inner = match.group(2)
    # 벗겨낸 안쪽이 또 다른 단일 래핑 펜스라면 한 번 더 처리한다(이중 래핑 방지).
    return strip_wrapping_code_fence(inner)
