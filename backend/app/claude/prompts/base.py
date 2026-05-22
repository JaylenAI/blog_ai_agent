from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.formats.schema import FormatSpec


class PromptTemplate(ABC):
    @abstractmethod
    def render(self, **kwargs: str) -> str: ...

    def _format_block(self, format_spec: FormatSpec | None) -> str:
        if not format_spec:
            return ""

        sections = ", ".join(format_spec.structure.required_sections)
        sc = format_spec.structure.section_count
        cc = format_spec.structure.char_count

        return f"""
[FORMAT: {format_spec.name} ({format_spec.id})]
{format_spec.prompt_instructions}

[STRUCTURE RULES — {format_spec.name}]
- 필수 섹션: {sections}
- 섹션 수: {sc.min}~{sc.max}개
- 표준 분량: {cc.standard[0]:,}~{cc.standard[1]:,}자 / 장문: {cc.long[0]:,}~{cc.long[1]:,}자
- 서두 스타일: {format_spec.structure.intro_style}
- 마무리 스타일: {format_spec.structure.closing_style}
- 표(HTML <table>): 최소 {format_spec.elements.tables_min}개
- 코드 블록: {format_spec.elements.code_blocks[0]}~{format_spec.elements.code_blocks[1]}개
"""
